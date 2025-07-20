#这个文件是用来批量筛选AI风险新闻的
#通过调用qwen2.5模型进行AI风险关键词第一轮筛选，将导入库的文件来源改为callmodel即可实现第一轮筛选操作
#通过调用qwen3模型进行AI风险关键词第二轮筛选
#注意调用模型的方式
#这里是调用本地模型的方式
#注意修改相关的路径和配置
#请确保已经安装了所需的库和模型
import os
import time
import json
import logging
import asyncio
import random
from pathlib import Path
from bs4 import BeautifulSoup
import numpy as np
from callmodel_qwen3 import call_model
#from callmodel import call_model
import re
# 🚀 必须在导入 torch 和 transformers 之前设置
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # 只用 GPU 0
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"  # 减少显存碎片
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # 关闭 tokenizer 并行警告
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

BASE_INPUT_DIR = "BASE_INPUT_DIR"  # 替换为实际的输入目录
BASE_OUTPUT_DIR = "BASE_OUTPUT_DIR"  # 替换为实际的输出目录

# === 日志设置 ===
LOG_FILE = "batch_processing.log" # 替换为实际的日志文件路径
ERROR_LOG_FILE = "error.log"
#BATCH_SIZE = 10
CONTENT_LIMIT = 10000
SELECTED_YM = ["2022/5","2022/6","2022/7","2022/8","2022/9","2022/10","2022/11","2022/12"]  # 选择要处理的年月
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# === 全局推理计数器 ===
global_inference_counter = 0

# 设置 logger
logger = logging.getLogger("batch_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # 防止重复输出到 stdout

# 清除已有的 handlers（防止多次运行脚本时重复添加）
if logger.hasHandlers():
    logger.handlers.clear()

# 文件 handler
file_handler = logging.FileHandler(LOG_FILE, mode='w')  # mode='a' 表示追加写入
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 控制台 handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# 错误 handler
error_handler = logging.FileHandler(ERROR_LOG_FILE, mode='w')
error_handler.setLevel(logging.WARNING)
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(error_handler)


PROMPT = """# 🔍 角色：AI内容风险管理与文本分类专家

## 🧠 简介
- **语言能力**：多语言支持  
- **职责概述**：识别并分类涉及AI技术（如自动驾驶、语言模型、机器人、无人机、深度学习等）的风险性内容。分析数据隐私、来源合法性、算法偏见、合规问题、法律伦理等方面的潜在风险。
- **专业背景**：计算机科学学位，辅修伦理学；具备AI风险评估、伦理审查与合规审计经验；曾参与AI伦理与风险研究项目。
- **个性特征**：严谨、注重细节、分析力强；致力于推动AI技术的负责任部署。
- **目标用户**：AI开发者、内容审核员、政策制定者、技术公司等。

## 🧩 核心技能

### 1. AI风险识别
- 精准识别AI相关内容中的法律、伦理、隐私等风险因素。
- 审核数据使用的合法性与合规性。

### 2. 文本分类
- 判定文本是否与AI风险直接相关。
- 运用自然语言处理技术实现自动分类。

## 📋 判断规则

### 1. 输入结构
- 每项内容包含“标题”及“部分正文”。

### 2. 相关性标准
- 明确提及AI技术（如语言模型、自动驾驶、深度学习等）。
- 内容需涉及具体风险：隐私泄露、偏见歧视、法律责任、数据合规、跨境风险、伦理道德问题等。
- 未具体指涉风险的内容（如泛泛描述AI应用）视为无关。

### 3. 排除标准
- 无关主题（如普通教育、医疗、经济报道中泛指AI的内容）。
- 内容未涉及AI相关风险，仅为技术描述或泛用场景。

## ⚙️ 工作流程

### 🎯 目标
判断接收的5条文章是否与AI风险**直接相关**。

### 🔎 步骤
1. 接收包含标题与正文的文章列表。
2. 对每项进行内容分析：
   - 是否提及AI技术；
   - 是否明确包含风险点（隐私、偏见、法律、伦理等）。
3. 根据判断输出分类结果,如果与AI风险**直接相关**，输出"AIGCrisk_relevant",如果不相关，输出"AIGCrisk_Irrelevant"。
### 📤 输入格式
- 一个json格式的字符串
- json字符串中包含5个对象，表示5篇文章。
- 其中每个对象包含两个字段：
  - `"title"`：文章标题
  - `"content"`：文章正文
####示例输入：
- '[{"title": "标题1", "content": "正文1"}, 
{"title": "标题2", "content": "正文2"},
{"title": "标题3", "content": "正文3"},
{"title": "标题4", "content": "正文4"},
{"title": "标题5", "content": "正文5"}]'
### 📤 输出格式
- 仅返回一个json格式的字符串
- 返回一个列表，列表中包含5个字符串，表示每篇文章的分类结果。
- 回答结果的每一项有且只有两种回答.1)`"AIGCrisk_relevant"`：明确涉及AI风险。2)`"AIGCrisk_Irrelevant"`：不涉及AI风险或表述模糊不明。
- 返回结果的列表元素个数应该与输入的列表元素数量一致！！！！！！
- 返回结果的列表回答的顺序应该与输入的列表元素顺序一致，即回答结果的第一项对应输入的第一项，第二项对应第二项，以此类推。
#### 示例输出：
["AIGCrisk_relevant", "AIGCrisk_Irrelevant", "AIGCrisk_Irrelevant", "AIGCrisk_Irrelevant", "AIGCrisk_Irrelevant"]

##注意事项
- 只返回一个json格式的字符串列表
- 仅返回分类结果，不要返回任何额外的文本或解释。
- 确保输出格式正确，避免多余的空格或换行。
- 如果无法判断，请返回 `"AIGCrisk_Irrelevant"`。
""" 


def extract_title(html: str) -> str:
    try:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.title.text.strip() if soup.title else ""
    except Exception as e:
        logger.warning(f"标题提取失败: {e}")
        return ""

def get_txt_summary(txt_path: Path) -> (str, str):
    try:
        text = txt_path.read_text(encoding='utf-8', errors='ignore').strip()
        start = time.time()
        if len(text) < 100:
            return "", text
        inputs = tokenizer([text.replace("\n", " ")], max_length=1024, return_tensors="pt", truncation=True).to(DEVICE)
        summary_ids = model.generate(inputs["input_ids"], max_length=150, min_length=80, length_penalty=2.0, num_beams=4, early_stopping=True)
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        end = time.time()
        logger.info(f"[摘要] {txt_path.name} 总耗时：{end - start:.2f} 秒")
        return summary, text
    except Exception as e:
        logger.warning(f"摘要生成失败: {e}")
        return "", ""

async def detect_ai_risk_batches(text_batches, system_prompt=PROMPT):
    def fetch_model_response(texts):
        global global_inference_counter
        try:
            formatted_input = texts  # 这里是 JSON 格式的文本
            thinking,response,tokens= call_model(system_prompt, formatted_input)#将思考和正式回答分开
            # 计数推理次数
            global_inference_counter += 1
            if global_inference_counter % 1000 == 0:
                logger.info(f"🚦 已推理 {global_inference_counter} 次，休眠 120 秒以防止堵塞...")
                time.sleep(120)  # 用 time.sleep 这里就够了，因为是在同步部分
            return thinking,response,tokens
        except Exception as e:
            logger.error(f"🛑 本地模型请求失败: {e}")
            return (["AIGCrisk_Irrelevant"] * len(texts), 0)

    async def fetch(texts):
        for attempt in range(3):
            try:
                start=time.time()
                thinking,response_str,tokens= fetch_model_response(texts)
                end=time.time()
                logger.info(f"[Model] 批次推理完成,用时{end-start:.2f}秒")
                #print(f"response_str: 1{response_str}2")
                if not response_str:
                    logger.warning(f"⚠️ 响应为空或缺少 'response' 字段:")
                    return (["AIGCrisk_Irrelevant"] * len(texts), 0)

                if isinstance(response_str, str):
                    try:
                        start_idx = response_str.find('[')
                        end_idx = response_str.rfind(']')
                        if start_idx != -1 and end_idx != -1:
                            list_str = response_str[start_idx:end_idx + 1]
                            if list_str.startswith('"') and list_str.endswith('"'):
                                list_str = list_str[1:-1]
                            response_list = json.loads(list_str)
                            return response_list,tokens
                        else:
                            logger.warning(f"⚠️ 响应中缺少中括号: {response_str[:]}")
                    except Exception as e:
                        logger.warning(f"⚠️ 响应解析失败: {e}\n原始 response 字符串: {response_str[:]}")
            except TimeoutError as e:
                logger.error(f"⏱️ API 请求超时（第 {attempt+1} 次）: {e}")
            except Exception as e:
                logger.error(f"🛑 未知错误（第 {attempt+1} 次）: {type(e).__name__}: {e}")
            await asyncio.sleep(1)
        return (["AIGCrisk_Irrelevant"] * len(texts), 0)
    tasks = [fetch(batch) for batch in text_batches]
    return await asyncio.gather(*tasks)
# 将输入格式转换为 JSON，结构化的发送给模型
def prepare_input_for_model(batch_data):
    # 格式化输入为 JSON，每个新闻为一个对象，包括标题和正文
    input_data = [{"title": title, "content": content} for _, title, content in batch_data]
    return json.dumps(input_data, ensure_ascii=False)

async def handle_batch(batch_data, output_dir):
    #批次推理与文件处理
    texts = prepare_input_for_model(batch_data)
    results_and_tokens = await detect_ai_risk_batches([texts])
    relevant_count = 0
    results, total_tokens = results_and_tokens[0]
    for (fpath, title, original_txt), result in zip(batch_data, results):
        logger.info(f"文件已处理: {fpath.stem}.txt | 结果: {result}")
    # 记录本批次的 tokens
    logger.info(f"本批次使用tokens: {total_tokens}")
    for (fpath, title, original_txt), result in zip(batch_data, results):
        if result == 'AIGCrisk_relevant':
            try:
                #print(f"路径{fpath}")
                combined = f"{title}\n{original_txt}"[:CONTENT_LIMIT]
                out_path = output_dir / f"{fpath.stem}.txt"
                #print(f"输出路径: {out_path}")
                if out_path.exists():
                    logger.warning(f"文件已存在，拒绝覆盖: {out_path}")
                    continue
                else:
                    out_path.write_text(combined, encoding="utf-8", errors="ignore")

                logger.info(f"✅ 保存风险文本: {fpath.stem}.txt ")
                relevant_count += 1
            except Exception as e:
                logger.error(f"❌ 保存失败: {e}")
    return relevant_count,total_tokens

async def main():
    start = time.time()
    total_files = 0
    relevant_files = 0
    total_tokens_per_batch = {5: []}  # 用于存储不同批次的tokens数量
    #Path(SUMMARY_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    #print("1")
    ym_dirs = [Path(BASE_INPUT_DIR) / ym   for ym in SELECTED_YM if (Path(BASE_INPUT_DIR) / ym ).is_dir()]
    for ym_dir in ym_dirs:
        #print("1")
        txt_files = list(ym_dir.glob("*.txt"))
        if not txt_files:
            
            continue

        #txt_files = random.sample(txt_files, min(len(txt_files), 3600))
        #用于随机抽取文件进行筛选的测试

        logger.info(f"处理目录: {ym_dir} 随机抽取 {len(txt_files)} 个文件")

        rel_path = ym_dir.relative_to(BASE_INPUT_DIR)
        #print(f"相对路径: {rel_path}")
        output_dir = Path(BASE_OUTPUT_DIR) / rel_path
        #print(f"输出目录: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

        batch_data = []
        for batch_size in [5]:  # 依次测试批次大小为5, 10, 15的情况  这里是在尝试测量批次对模型推理的影响，可以不用更改
            logger.info(f"开始处理批次大小: {batch_size}")
            for txt_path in txt_files:
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        title = f.readline().strip()
                        content = f.read().strip()


                    batch_data.append((txt_path,title,content))
                    logger.info(f"添加到批次: {txt_path.name} | 批次大小: {len(batch_data)}")
                    if len(batch_data) >= batch_size:
                        relevant_count, batch_tokens = await handle_batch(batch_data, output_dir)
                        relevant_files += relevant_count
                        total_files += len(batch_data)
                        total_tokens_per_batch[batch_size].append(batch_tokens)  # 记录每个批次的tokens数量
                        batch_data.clear()  # 清空batch_data，准备下一个批次

                except Exception as e:
                    logger.error(f"处理文件失败 {txt_path}: {e}")

            # 处理剩余的文件
            if batch_data:
                relevant_count, batch_tokens = await handle_batch(batch_data, output_dir)
                relevant_files += relevant_count
                total_files += len(batch_data)
                total_tokens_per_batch[batch_size].append(batch_tokens)  
    # 计算每种批次大小的平均tokens
    for batch_size, tokens_list in total_tokens_per_batch.items():
        avg_tokens = np.mean(tokens_list) if tokens_list else 0
        logger.info(f"批次大小 {batch_size}: 平均使用 {avg_tokens:.2f} tokens")
    logger.info(f"🕒 总耗时：{time.time() - start:.2f}s")
    if total_files > 0:
        rate = 100 * relevant_files / total_files
        logger.info(f"📊 总共处理 {total_files} 篇新闻，风险相关 {relevant_files} 篇，比例 {rate:.2f}%")
    else:
        logger.info("📭 未处理任何文件")

if __name__ == "__main__":

    asyncio.run(main())
