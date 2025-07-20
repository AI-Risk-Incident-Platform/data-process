#这个文件是用来调用qwen3模型 用于  AI风险关键词第二轮筛选的
#这里是调用本地模型的方式
#请替换为实际的模型名称和API密钥
#如果是调用远程模型，请修改为远程API的调用方式

import time
import logging
from openai import OpenAI

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def call_model(system_prompt, user_prompt):
    # 请替换为实际的 EAS API KEY
    openai_api_key = "your_api_key_here"  # 替换为实际的API密钥
    # 请替换为实际的 EAS API Endpoint
    openai_api_base = "your_api_base_here"  # 替换为实际的API基础URL
    # 请替换为实际的模型名称
    model_name = "qwen3"

    client = OpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base
    )
    try:
        start_time = time.time()
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            top_p=0.8,
            presence_penalty=1.5,
            max_tokens = 4096,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}}
        )
        logging.info(f"Response time: {time.time() - start_time}")
        content = completion.choices[0].message.content
        tokens=completion.usage.total_tokens
        # 分离思考内容和正式回答
        start_index = content.find('<think>')
        end_index = content.find('</think>')

        if start_index != -1 and end_index != -1:
            thinking_part = content[start_index + len('<think>'):end_index]
            answer_part = content[end_index + len('</think>'):].strip()
            return thinking_part, answer_part,tokens
        return None, content,tokens

    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None, None,None
