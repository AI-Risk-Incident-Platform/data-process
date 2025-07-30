import time
import logging
import os
import json
import asyncio
from typing import Tuple, Optional
from openai import OpenAI

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("doubao_model_calls.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def call_model(
    system_prompt: str, 
    user_prompt: str,
    model_name: str = "doubao-1-5-pro-32k-250115",
    temperature: float = 0.7,
    max_retries: int = 3
) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    调用豆包API进行AI风险关键词筛选
    
    参数:
        system_prompt: 系统提示词，定义模型角色和任务
        user_prompt: 用户输入的待处理内容
        model_name: 模型名称
        temperature: 生成温度，控制输出随机性
        max_retries: 最大重试次数
    
    返回:
        thinking_part: 模型思考过程
        answer_part: 模型正式回答
        tokens: 消耗的token数量
    """
    # 从环境变量获取配置或使用默认值
    llm_url = os.getenv("LLM_URL", "https://ark.cn-beijing.volces.com/api/v3")
    api_key = os.getenv("API_KEY", "28be7d5d-b9c9-4cc8-8ac8-528aa0870790")

    # 配置检查
    if api_key == "28be7d5d-b9c9-4cc8-8ac8-528aa0870790":
        logger.warning("使用默认API密钥，可能无法正常工作，请替换为实际密钥")
    
    client = OpenAI(
        base_url=llm_url,
        api_key=api_key
    )

    for attempt in range(max_retries):
        try:
            start_time = time.time()
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                top_p=0.8,
                max_tokens=4096
            )
            
            response_time = time.time() - start_time
            tokens_used = completion.usage.total_tokens if completion.usage else 0
            logger.info(
                f"豆包API调用成功 (尝试 {attempt+1}/{max_retries}) "
                f"| 耗时: {response_time:.2f}秒 "
                f"| Token消耗: {tokens_used}"
            )

            content = completion.choices[0].message.content
            
            # 豆包模型可能不使用特定思考标记，因此将所有内容视为回答
            return None, content.strip(), tokens_used

        except Exception as err:
            logger.error(
                f"豆包API调用失败 (尝试 {attempt+1}/{max_retries}) "
                f"| 错误类型: {type(err).__name__} "
                f"| 错误信息: {str(err)}"
            )
            
            # 重试前等待，指数退避策略
            if attempt < max_retries - 1:
                sleep_time = (attempt + 1) * 2  # 1st: 2s, 2nd: 4s
                logger.info(f"将在 {sleep_time} 秒后重试...")
                time.sleep(sleep_time)

    # 所有重试都失败
    logger.error(f"达到最大重试次数 ({max_retries})，调用失败")
    return None, None, None

# 批量处理函数，适配主程序
async def detect_ai_risk_batches(text_batches, system_prompt):
    """处理批量文本，调用豆包API进行AI风险检测"""
    def fetch_model_response(texts):
        try:
            # 调用豆包模型
            thinking, response_str, tokens = call_model(system_prompt, texts)
            return thinking, response_str, tokens
        except Exception as e:
            logger.error(f"模型请求失败: {e}")
            return (["AIGCrisk_Irrelevant"] * len(json.loads(texts)), 0)

    async def fetch(texts):
        for attempt in range(3):
            try:
                start = time.time()
                thinking, response_str, tokens = fetch_model_response(texts)
                end = time.time()
                logger.info(f"[豆包模型] 批次推理完成,用时{end-start:.2f}秒")

                if not response_str:
                    logger.warning(f"响应为空: {response_str}")
                    return (["AIGCrisk_Irrelevant"] * len(json.loads(texts)), 0)

                # 解析豆包返回的JSON结果
                try:
                    # 查找JSON数组的开始和结束位置
                    start_idx = response_str.find('[')
                    end_idx = response_str.rfind(']')
                    if start_idx != -1 and end_idx != -1:
                        list_str = response_str[start_idx:end_idx + 1]
                        response_list = json.loads(list_str)
                        return response_list, tokens
                    else:
                        logger.warning(f"响应中缺少有效的JSON数组: {response_str[:100]}...")
                except Exception as e:
                    logger.warning(f"响应解析失败: {e}\n原始响应: {response_str[:100]}...")
            except Exception as e:
                logger.error(f"处理失败（第 {attempt+1} 次）: {e}")
            await asyncio.sleep(1)
        # 如果所有尝试都失败，返回默认结果
        return (["AIGCrisk_Irrelevant"] * len(json.loads(texts)), 0)

    tasks = [fetch(batch) for batch in text_batches]
    return await asyncio.gather(*tasks)

# 测试代码
if __name__ == "__main__":
    # 测试豆包API调用
    test_system = """# 🔍 角色：AI内容风险管理与文本分类专家

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
    test_user = json.dumps([
        {"title": "AI算法歧视问题研究", "content": "本文讨论了AI算法中存在的歧视问题及其社会影响"},
        {"title": "普通计算机技术发展", "content": "本文介绍了传统计算机技术的发展历程"},
        {"title": "生成式AI的版权争议", "content": "大语言模型训练数据涉及大量未经授权的作品，引发法律纠纷"},
        {"title": "自动驾驶安全事故分析", "content": "某品牌自动驾驶系统因算法缺陷导致交通事故"},
        {"title": "Python编程入门教程", "content": "介绍Python基础语法和变量定义"}
    ], ensure_ascii=False)
    
    async def test():
        # 调用模型获取结果
        results = await detect_ai_risk_batches([test_user], test_system)
        parsed_results, tokens = results[0]
        
        # 打印模型原始输出（关键新增部分）
        print("\n===== 模型原始输出 =====")
        # 重新调用一次模型，专门打印原始响应
        thinking, raw_response, _ = call_model(test_system, test_user)
        print(raw_response)
        
        # 打印解析后的结果
        print("\n===== 解析后的结果 =====")
        print(parsed_results)
        print(f"\nToken消耗: {tokens}")
    
    asyncio.run(test())