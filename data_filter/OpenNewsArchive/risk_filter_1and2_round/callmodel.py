#这个文件是用来调用qwen2.5模型 用于  AI风险关键词第一轮筛选的
#这里是调用本地模型的方式
#请替换为实际的模型名称和API密钥
#如果是调用远程模型，请修改为远程API的调用方式

from openai import OpenAI# 直接调用本地大模型接口的方式
def call_model(system_prompt, user_prompt):
    LLM_url="LLM_url" #请替换为实际的LLM服务地址

    
    client = OpenAI(base_url=LLM_url, api_key="api_key")  # 请替换为实际的API密钥

    completion = client.chat.completions.create(
        model="qwen2.5-instruct-custom",
        messages=[        
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        ,timeout=120,
        max_tokens = 8192

    )
    response=completion.choices["message"]["content"]
    tokens=completion.usage.total_tokens
    return response, tokens

