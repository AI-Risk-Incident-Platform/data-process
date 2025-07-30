import os
import time
import json
import logging
import asyncio
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from callmodel_doubao import call_model, detect_ai_risk_batches  # 豆包API调用模块
# 注意根据实际调用的API修改导入路径和函数名

# 环境变量设置
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 配置参数
BASE_INPUT_DIR = "/data3/downloads/cc-news"  # 输入根目录
BASE_OUTPUT_DIR = "/data3/downloads/cc-news-risks_batch2_notthink"  # 输出根目录
LOG_FILE = "batch_processing_2025_5-6month.log"
ERROR_LOG_FILE = "error.log"
CONTENT_LIMIT = 10000
SELECTED_YM = ["2025/5", "2025/6"]  # 需处理的年月
import threading  # 用于线程安全的计数器

# 环境变量和配置参数不变（仅修改MAX_PROCESSES为MAX_THREADS）
MAX_THREADS = 5  # 线程数（可根据API并发限制调整，建议5-10）
BATCH_SIZE = 5  # 每批处理5个文件（与提示词一致）

# 日志配置
def setup_logger():
    logger = logging.getLogger("batch_logger")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.hasHandlers():
        logger.handlers.clear()

    # 文件和控制台日志
    file_handler = logging.FileHandler(LOG_FILE, mode='w')
    console_handler = logging.StreamHandler()
    error_handler = logging.FileHandler(ERROR_LOG_FILE, mode='w')

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(processName)s - %(message)s')
    for handler in [file_handler, console_handler, error_handler]:
        handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addHandler(error_handler)

    return logger

logger = setup_logger()

# 提示词
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

## ⚙ 工作流程

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

def prepare_input_for_model(batch_data):
    """格式化输入为5条文章的JSON列表"""
    input_data = [{"title": title, "content": content} for _, title, content in batch_data]
    return json.dumps(input_data, ensure_ascii=False)

async def process_single_batch(batch_data, output_root):
    """处理单个批次，输出路径不含texts文件夹"""
    try:
        texts = prepare_input_for_model(batch_data)
        results_and_tokens = await detect_ai_risk_batches([texts], PROMPT)
        relevant_count = 0
        results, total_tokens = results_and_tokens[0]

        if len(results) != len(batch_data):
            logger.warning(f"结果长度不匹配，预期{len(batch_data)}，实际{len(results)}")
            return 0, total_tokens

        for (fpath, title, original_txt), result in zip(batch_data, results):
            if result == 'AIGCrisk_relevant':
                try:
                    # 关键调整：输出路径去掉texts层级
                    # 输入文件路径示例：BASE_INPUT_DIR/2022/5/texts/news_001.txt
                    parent_dir = fpath.parent  # 得到"BASE_INPUT_DIR/2022/5/texts"
                    year_month_dir = parent_dir.parent  # 得到"BASE_INPUT_DIR/2022/5"
                    rel_path = year_month_dir.relative_to(BASE_INPUT_DIR)  # 得到"2022/5"
                    output_dir = Path(output_root) / rel_path  # 输出目录：BASE_OUTPUT_DIR/2022/5
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    out_path = output_dir / f"{fpath.stem}.txt"
                    if not out_path.exists():
                        combined = f"{title}\n{original_txt}"[:CONTENT_LIMIT]
                        out_path.write_text(combined, encoding="utf-8", errors="ignore")
                        relevant_count += 1
                except Exception as e:
                    logger.error(f"保存文件失败 {fpath}: {e}")

        return relevant_count, total_tokens
    except Exception as e:
        logger.error(f"批次处理失败: {e}")
        return 0, 0

def worker_thread(batch, output_root, counter_lock, global_counter):
    """线程工作函数（替代原worker_process）"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        relevant_count, tokens = loop.run_until_complete(
            process_single_batch(batch, output_root)
        )
        loop.close()
        
        # 线程安全更新计数器（用threading.Lock）
        with counter_lock:
            global_counter[0] += 1  # 用列表存储计数器，实现可变对象共享
            current = global_counter[0]
            if current % 100 == 0:  # 每100批次输出一次进度（更频繁监控）
                logger.info(f"全局已处理 {current} 批次")
            if current % 1000 == 0:
                logger.info(f"全局已处理 {current} 批次，休眠120秒...")
                time.sleep(120)
                
        return relevant_count, len(batch), tokens
    except Exception as e:
        logger.error(f"线程处理失败: {e}")
        return 0, len(batch), 0

def main():
    start = time.time()
    
    # 1. 收集文件（逻辑不变）
    all_files = []
    for ym in SELECTED_YM:
        ym_dir = Path(BASE_INPUT_DIR) / ym
        if not ym_dir.is_dir():
            logger.warning(f"年月目录不存在：{ym_dir}")
            continue
        
        texts_dir = ym_dir / "texts"
        if not texts_dir.exists() or not texts_dir.is_dir():
            logger.info(f"无texts文件夹，跳过：{ym_dir}")
            continue
        
        txt_files = list(texts_dir.rglob("*.txt"))  # 递归查找
        all_files.extend(txt_files)
        logger.info(f"从 {texts_dir} 收集到 {len(txt_files)} 个文件")
    
    if not all_files:
        logger.info("未找到任何txt文件，退出")
        return
    
    logger.info(f"共收集 {len(all_files)} 个文件，使用 {MAX_THREADS} 线程处理")
    
    # 2. 创建输出目录（不变）
    output_root = Path(BASE_OUTPUT_DIR)
    output_root.mkdir(parents=True, exist_ok=True)
    
    # 3. 划分批次（不变）
    batches = []
    for i in range(0, len(all_files), BATCH_SIZE):
        batch_files = all_files[i:i+BATCH_SIZE]
        batch_data = []
        for fpath in batch_files:
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    title = f.readline().strip()
                    content = f.read().strip()
                batch_data.append((fpath, title, content))
            except Exception as e:
                logger.error(f"读取文件失败 {fpath}: {e}")
        if batch_data:
            batches.append(batch_data)
    
    logger.info(f"文件已分为 {len(batches)} 个批次（每批最多{5}个）")
    
    # 4. 多线程处理（核心修改）
    global_counter = [0]  # 用列表实现线程间共享的计数器（可变对象）
    counter_lock = threading.Lock()  # 线程安全的锁
    
    # 用ThreadPoolExecutor替代Pool
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # 构建线程任务参数（传递锁和计数器）
        worker_args = [
            (batch, output_root, counter_lock, global_counter) 
            for batch in batches
        ]
        # 提交所有任务并获取结果
        results = list(executor.map(
            lambda x: worker_thread(x[0], x[1], x[2], x[3]), 
            worker_args
        ))
    
    # 5. 汇总结果（不变）
    total_relevant = 0
    total_processed = 0
    total_tokens = 0
    for rel, processed, tokens in results:
        total_relevant += rel
        total_processed += processed
        total_tokens += tokens
    
    # 输出统计（不变）
    duration = time.time() - start
    logger.info(f"\n===== 处理完成 =====")
    logger.info(f"总耗时: {duration:.2f}秒")
    logger.info(f"总处理文件: {total_processed}")
    logger.info(f"风险相关文件: {total_relevant}")
    if total_processed > 0:
        logger.info(f"相关比例: {100 * total_relevant / total_processed:.2f}%")
    logger.info(f"总Token消耗: {total_tokens}")

if __name__ == "__main__":
    main()