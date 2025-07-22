import os
import json
import copy
import glob
import numpy as np
from openai import OpenAI
from scipy.spatial.distance import cosine
from collections import defaultdict
import logging
# 屏蔽 httpx、urllib3、openai、dashscope 等库的 INFO 日志，只显示 WARNING 及以上
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("dashscope").setLevel(logging.WARNING)

# 输入输出目录
# data_dir = "incidentinfo-muti"
data_dir = "test-entity"
out_dir = "output/EA-output"
os.makedirs(out_dir, exist_ok=True)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(out_dir, "process.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 嵌入API调用
client = OpenAI(
    api_key='28be7d5d-b9c9-4cc8-8ac8-528aa0870790',
    base_url="https://ark.cn-beijing.volces.com/api/v3"
)

def get_embedding(text):
    response = client.embeddings.create(
        model="doubao-embedding-large-text-250515",
        input=text,
        dimensions=1024,
        encoding_format="float"
    )
    return response.data[0].embedding

# 兼容enable_thinking参数的LLM调用

def call_llm_with_optional_thinking(client, model, messages, temperature=0.0):
    try:
        return client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            enable_thinking=False
        )
    except TypeError as e:
        if "enable_thinking" in str(e):
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
        else:
            raise

# 1. 实体抽取函数
def extract_entities(data_dir):
    en_name_list = []
    en_name_to_category = {}
    en_name_to_event_ids = defaultdict(set)
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.startswith("entity_incident") and file.endswith(".json"):
                file_path = os.path.join(root, file)
                # 获取事件id（假设为父目录名或文件名中的数字）
                event_id = os.path.basename(root)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        logging.error(f"读取文件失败: {file_path}, 错误: {e}")
                        continue
                    event_concepts = data.get("事件概念", {})
                    for category, entity in event_concepts.items():
                        en_name = entity.get("英文名称")
                        if not en_name:
                            continue
                        en_name_list.append(en_name)
                        en_name_to_category[en_name] = category
                        en_name_to_event_ids[en_name].add(event_id)
    en_name_list = list(set(en_name_list))
    en_name_to_old_id = {name: idx+1 for idx, name in enumerate(en_name_list)}
    # 把 set 转成 list
    en_name_to_event_ids = {k: list(v) for k, v in en_name_to_event_ids.items()}
    return en_name_list, en_name_to_category, en_name_to_old_id, en_name_to_event_ids

# 2. 向量嵌入函数
def embed_entities(en_name_list, get_embedding_func):
    embeddings = {}
    for name in en_name_list:
        try:
            embeddings[name] = get_embedding_func(name)
        except Exception as e:
            logging.error(f"向量化失败: {name}, 错误: {e}")
    return embeddings

# 新增：计算每个实体的top k相似实体
def get_top_k_similar_entities(en_name_list, embeddings, k=5):
    """
    返回格式：{
        en_name: [(other_en_name, sim_score), ...]  # 长度为k
    }
    """
    topk_dict = {}
    for i, name1 in enumerate(en_name_list):
        emb1 = embeddings[name1]
        sims = []
        for j, name2 in enumerate(en_name_list):
            if i == j:
                continue
            emb2 = embeddings[name2]
            sim = 1 - cosine(emb1, emb2)
            sims.append((name2, sim))
        # 取top k
        sims.sort(key=lambda x: x[1], reverse=True)
        topk_dict[name1] = sims[:k]
    return topk_dict

# 预留：大模型判断是否为同一实体
def judge_entity_equivalence_with_llm(entity, topk_entities, client, similarity_threshold=0.8):
    """
    entity: str
    topk_entities: List[Tuple[str, float]]
    返回：List[bool]，与topk_entities一一对应，True表示同一实体
    """
    results = []
    for other_entity, sim in topk_entities:
        if sim < similarity_threshold:
            results.append(False)
            continue
        prompt = (
            f"Are the following two entities referring to the same real-world entity?\n"
            f"Entity 1: '{entity}'\n"
            f"Entity 2: '{other_entity}'\n"
            f"Answer with 'Yes' or 'No'."
        )
        try:
            response = call_llm_with_optional_thinking(
                client,
                model="doubao-1-5-pro-32k-250115",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            answer = response.choices[0].message.content.strip().lower()
            is_same = ("yes" in answer)
            results.append(is_same)
        except Exception as e:
            logging.error(f"LLM判断失败: {entity} vs {other_entity}, 错误: {e}")
            results.append(False)
    return results

# 并查集工具类
def find(parents, x):
    if parents[x] != x:
        parents[x] = find(parents, parents[x])
    return parents[x]

def union(parents, x, y):
    px, py = find(parents, x), find(parents, y)
    if px != py:
        parents[py] = px

# 根据大模型判断结果合并实体为簇
def merge_entities_by_llm_judgement(en_name_list, topk_dict, llm_judgement_dict):
    # 初始化并查集
    parents = {name: name for name in en_name_list}
    for name, topk in topk_dict.items():
        for idx, (other_name, _) in enumerate(topk):
            if llm_judgement_dict[name][idx]:
                union(parents, name, other_name)
    # 收集簇
    clusters = {}
    for name in en_name_list:
        root = find(parents, name)
        clusters.setdefault(root, []).append(name)
    return list(clusters.values())

# 大模型命名实体簇
def name_entity_clusters_with_llm(clusters, client):
    """
    clusters: List[List[en_name]]
    返回：{cluster_idx: cluster_name}
    """
    cluster_names = {}
    for idx, cluster in enumerate(clusters):
        if len(cluster) == 1:
            # 只有一个实体的簇，直接用实体名作为簇名
            cluster_names[idx] = cluster[0]
            continue
        names_str = ", ".join(cluster)
        prompt = (
            f"Given the following list of entity names that refer to the same concept, please extract their most essential commonality and generate the shortest possible English name that best summarizes this group. "
            f"Entity names: {names_str}\n"
            f"Return only the name, as short as possible."
        )
        try:
            response = call_llm_with_optional_thinking(
                client,
                model="doubao-1-5-pro-32k-250115",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            cluster_name = response.choices[0].message.content.strip()
            cluster_names[idx] = cluster_name
        except Exception as e:
            logging.error(f"LLM命名实体簇失败: {cluster}, 错误: {e}")
            cluster_names[idx] = f"Cluster_{idx+1}"
    return cluster_names

# 3. 相似度计算函数
def cluster_entities(en_name_list, embeddings, threshold=0.8):
    clusters = []
    used = set()
    for i, name1 in enumerate(en_name_list):
        if name1 in used:
            continue
        cluster = [name1]
        used.add(name1)
        emb1 = embeddings[name1]
        for j, name2 in enumerate(en_name_list):
            if i == j or name2 in used:
                continue
            emb2 = embeddings[name2]
            sim = 1 - cosine(emb1, emb2)
            if sim >= threshold:
                cluster.append(name2)
                used.add(name2)
        clusters.append(cluster)
    return clusters

# 4. 实体对齐函数
def align_entities(clusters, en_name_to_category, data_dir, out_dir, en_name_to_old_id, en_name_to_event_ids, cluster_names):
    # 1. 先遍历所有entity_incident*.json，记录每个en_name的old_entity_id（如无则用en_name_to_old_id）
    en_name_to_json_id = {}
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.startswith("entity_incident") and file.endswith(".json") and not file.endswith("_aligned.json"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        logging.error(f"读取文件失败: {file_path}, 错误: {e}")
                        continue
                    event_concepts = data.get("事件概念", {})
                    for category, entity in event_concepts.items():
                        en_name = entity.get("英文名称")
                        if not en_name:
                            continue
                        en_name_to_json_id[en_name] = entity.get("entity_id")

    # 2. 聚类后每簇分配new_entity_id，并用大模型命名的簇名作为对齐后英文名称
    aligned_en_name_map = {}  # en_name -> 大模型命名的簇名
    for idx, cluster in enumerate(clusters):
        cluster_name = cluster_names[idx]
        for name in cluster:
            aligned_en_name_map[name] = cluster_name  # 用大模型命名的簇名

    # 3. 生成entity_alignment，包含entity_id、category、source_event_ids
    entity_alignment = {}
    for name in aligned_en_name_map:
        old_id = en_name_to_json_id.get(name)
        if old_id is None:
            old_id = en_name_to_old_id.get(name)
        event_ids = en_name_to_event_ids.get(name, [])
        entity_alignment[name] = {
            "entity_id": old_id,  # 字段名改为entity_id
            "category": en_name_to_category[name],
            "source_event_ids": event_ids  # 保留所有事件id
        }

    # 4. 输出对齐结果
    out_path = os.path.join(out_dir, "entity_alignment.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(entity_alignment, f, ensure_ascii=False, indent=2)
    logging.info(f"实体对齐结果已保存到: {out_path}")

    # 5. 写回原始json文件，另存为_aligned.json，英文名称写对齐后名称，并新增“实体对齐后事件属性”
    changed_event_ids = set()
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.startswith("entity_incident") and file.endswith(".json") and not file.endswith("_aligned.json"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        logging.error(f"读取文件失败: {file_path}, 错误: {e}")
                        continue
                    event_concepts = data.get("事件概念", {})
                    pre_entity_ids = {}
                    aligned_entity_names = {}
                    for category, entity in event_concepts.items():
                        en_name = entity.get("英文名称")
                        if not en_name:
                            continue
                        pre_entity_ids[en_name] = entity.get("entity_id")
                        # 对齐写入
                        if en_name in entity_alignment:
                            # 不再写entity_id，只替换英文名称为大模型命名的簇名
                            entity["英文名称"] = aligned_en_name_map[en_name]
                        # 构造实体对齐后事件属性：深拷贝，替换英文名称
                        aligned_entity = entity.copy()
                        if en_name in aligned_en_name_map:
                            aligned_entity["英文名称"] = aligned_en_name_map[en_name]
                        aligned_entity_names[category] = aligned_entity
                    # 新增“实体对齐后事件属性”
                    data["实体对齐后事件属性"] = aligned_entity_names
                # 保存新文件，只加一次_aligned
                new_file = file.replace('.json', '_aligned.json')
                new_path = os.path.join(root, new_file)
                with open(new_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                # 读取新文件进行对比
                with open(new_path, 'r', encoding='utf-8') as f:
                    try:
                        aligned_data = json.load(f)
                    except Exception as e:
                        logging.error(f"读取文件失败: {new_path}, 错误: {e}")
                        continue
                    aligned_event_concepts = aligned_data.get("事件概念", {})
                    for category, entity in aligned_event_concepts.items():
                        en_name = entity.get("英文名称")
                        if not en_name:
                            continue
                        pre_id = pre_entity_ids.get(en_name)
                        post_id = entity.get("entity_id")
                        if pre_id != post_id:
                            event_id = os.path.basename(root)
                            changed_event_ids.add(event_id)
                            break
    if changed_event_ids:
        pass
    else:
        logging.info("所有事件对齐前后entity_id均未发生变化。")

def save_entity_clusters(clusters, entity_alignment_path, out_path):
    # 1. 读取entity_alignment.json
    with open(entity_alignment_path, 'r', encoding='utf-8') as f:
        entity_alignment = json.load(f)
    # 2. 构建目标结构，只保留实体数大于1的簇，外层key为shortest_name
    result = {}
    for cluster in clusters:
        if len(cluster) <= 1:
            continue
        # 取该簇中名称长度最短的实体名
        shortest_name = min(cluster, key=lambda x: len(x))
        inner = {}
        for name in cluster:
            old_id = str(entity_alignment[name]["old_entity_id"])
            inner[old_id] = name
        result[shortest_name] = inner
    # 3. 写入json
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    logging.info(f"实体聚类簇已保存到: {out_path}")

if __name__ == "__main__":
    en_name_list, en_name_to_category, en_name_to_old_id, en_name_to_event_ids = extract_entities(data_dir)
    # 立即生成entity_alignment.json
    entity_alignment = {}
    for name in en_name_list:
        entity_alignment[name] = {
            "entity_id": en_name_to_old_id.get(name),
            "category": en_name_to_category[name],
            "source_event_ids": en_name_to_event_ids.get(name, [])
        }
    entity_alignment_path = os.path.join(out_dir, "entity_alignment.json")
    with open(entity_alignment_path, 'w', encoding='utf-8') as f:
        json.dump(entity_alignment, f, ensure_ascii=False, indent=2)
    logging.info(f"抽取实体内容已保存到: {entity_alignment_path}")
    # 1. 按类别分组
    category_to_names = defaultdict(list)
    for name in en_name_list:
        category = en_name_to_category[name]
        category_to_names[category].append(name)

    # 新增：分组处理所有后续流程
    all_clusters = []
    all_cluster_names = {}
    cluster_idx_offset = 0
    for category, names_in_cat in category_to_names.items():
        if len(names_in_cat) == 0:
            continue
        # 2. 计算该分类下实体的嵌入
        embeddings = embed_entities(names_in_cat, get_embedding)
        # 3. 计算每个实体的top k相似实体
        top_k = 5  # 可配置参数
        similarity_threshold = 0.85  # 新增：相似度阈值，低于此值则不使用LLM判断
        topk_dict = get_top_k_similar_entities(names_in_cat, embeddings, k=top_k)
        # 保存topk结果（可选，按分类保存）
        topk_out_path = os.path.join(out_dir, f"entity_top{top_k}_similar_{category}.json")
        with open(topk_out_path, 'w', encoding='utf-8') as f:
            json.dump({k: [(n, float(s)) for n, s in v] for k, v in topk_dict.items()}, f, ensure_ascii=False, indent=2)
        logging.info(f"[{category}] 每个实体的top{top_k}相似实体已保存到: {topk_out_path}")
        # 4. 大模型判断是否为同一实体
        llm_judgement_dict = {}
        for name, topk in topk_dict.items():
            llm_judgement_dict[name] = judge_entity_equivalence_with_llm(name, topk, client, similarity_threshold)
        # 5. 根据大模型判断结果合并实体为簇
        clusters = merge_entities_by_llm_judgement(names_in_cat, topk_dict, llm_judgement_dict)
        # 6. 大模型命名实体簇
        cluster_names = name_entity_clusters_with_llm(clusters, client)
        # 7. 合并所有分组的聚类和命名结果
        all_clusters.extend(clusters)
        # cluster_names的key是局部索引，需要全局唯一key
        for idx, cname in cluster_names.items():
            all_cluster_names[cluster_idx_offset + idx] = cname
        cluster_idx_offset += len(cluster_names)
    # 8. 生成对齐后的json文件（全局合并）
    align_entities(all_clusters, en_name_to_category, data_dir, out_dir, en_name_to_old_id, en_name_to_event_ids, all_cluster_names)

    # 新增：保存聚类命名结果到output/entity_clusters_named.json，结构与原文件一致
    # 读取entity_alignment.json，获取entity_id
    with open(os.path.join(out_dir, "entity_alignment.json"), 'r', encoding='utf-8') as fa:
        entity_alignment = json.load(fa)
    cluster_dict = {}
    for idx, cluster in enumerate(all_clusters):
        if len(cluster) <= 1:
            continue  # 只保留实体数大于1的簇
        cluster_name = all_cluster_names[idx]
        cluster_dict[cluster_name] = {}
        for name in cluster:
            if name in entity_alignment:
                entity_id = entity_alignment[name]["entity_id"]
                cluster_dict[cluster_name][str(entity_id)] = name
            else:
                logging.warning(f"实体名 {name} 不在 entity_alignment 中，已跳过。")
    cluster_out_path = os.path.join(out_dir, "entity_clusters_named.json")
    with open(cluster_out_path, 'w', encoding='utf-8') as f:
        json.dump(cluster_dict, f, ensure_ascii=False, indent=2)
    logging.info(f"命名后的实体簇已保存到: {cluster_out_path}")