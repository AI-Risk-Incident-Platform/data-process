import json
import plotly.graph_objects as go

# 读取 JSON 文件
data_path = 'output/entity_alignment.json'
with open(data_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取发生变化的实体
entities = []
for name, info in data.items():
    if info['old_entity_id'] != info['new_entity_id']:
        entities.append({
            'old_entity_id': info['old_entity_id'],
            'old_name': name,
            'new_entity_id': info['new_entity_id'],
            'category': info['category']
        })

# 统计每个 new_entity_id 被多少个 old_entity_id 指向
from collections import defaultdict
new_id_to_old_ids = defaultdict(set)
for e in entities:
    new_id_to_old_ids[e['new_entity_id']].add(e['old_entity_id'])

# 只保留有3个及以上 old_entity_id 指向的 new_entity_id
qualified_new_ids = {new_id for new_id, old_ids in new_id_to_old_ids.items() if len(old_ids) >= 2}

# 只保留这些 new_entity_id 相关的实体
filtered_entities = [e for e in entities if e['new_entity_id'] in qualified_new_ids]

# 构建 new_entity_id 到名称的映射（对齐后名称）
new_id_to_name = {}
for name, info in data.items():
    new_id_to_name[info['new_entity_id']] = name

if not filtered_entities:
    print('没有3个及以上 old_entity_id 指向同一个 new_entity_id 的实体。')
    exit(0)

# 左侧节点：所有 old_entity_id 对应的 old_name
old_id_name_pairs = {(e['old_entity_id'], e['old_name']) for e in filtered_entities}
old_id_name_list = sorted(list(old_id_name_pairs), key=lambda x: x[0])
old_names = [name for _, name in old_id_name_list]

# 右侧节点：所有 new_entity_id 对应的 new_name
new_id_name_pairs = {(e['new_entity_id'], new_id_to_name[e['new_entity_id']]) for e in filtered_entities}
new_id_name_list = sorted(list(new_id_name_pairs), key=lambda x: x[0])
new_names = [name for _, name in new_id_name_list]

node_labels = old_names + new_names

# 构建名称到节点索引的映射
old_name_to_index = {name: i for i, name in enumerate(old_names)}
new_name_to_index = {name: i + len(old_names) for i, name in enumerate(new_names)}

# 构建桑基图的 links
links = {
    'source': [],
    'target': [],
    'value': [],
    'label': []
}
for e in filtered_entities:
    old_name = e['old_name']
    new_name = new_id_to_name[e['new_entity_id']]
    links['source'].append(old_name_to_index[old_name])
    links['target'].append(new_name_to_index[new_name])
    links['value'].append(1)
    links['label'].append(e['category'])

# 创建桑基图
fig = go.Figure(go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=node_labels,
    ),
    link=dict(
        source=links['source'],
        target=links['target'],
        value=links['value'],
        label=links['label'],
    )
))

fig.update_layout(title_text="实体对齐前后名称变化桑基图（仅显示3个及以上old id合并的情况）", font_size=12)
fig.write_html('entity_id_sankey.html')
print('桑基图已保存为 entity_id_sankey.html') 