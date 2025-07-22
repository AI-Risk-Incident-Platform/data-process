# -*- coding: utf-8 -*-

import os
from openai import OpenAI
import json
from datetime import datetime
from ttl_visualization import visualize_ttl_file
import re
import time
import requests

def clean_filename(filename):
    # 移除换行符
    cleaned = filename.replace('\n', '_')
    # 移除不允许的字符
    # Windows不允许的字符: \ / : * ? " < > |
    cleaned = re.sub(r'[\\/:*?"<>|]', '', cleaned)
    # 将空格替换为下划线
    cleaned = cleaned.replace(' ', '_')
    # 移除多余的下划线
    cleaned = re.sub(r'_+', '_', cleaned)
    # 移除开头和结尾的下划线
    cleaned = cleaned.strip('_')
    return cleaned

def get_incident_data(incident_id):
    """从API获取指定incident_id的事件数据"""
    try:
        response = requests.get(f"http://10.101.171.106:9000/incidents/{incident_id}")
        return response.json()
    except Exception as e:
        print(f"获取事件数据时发生错误: {str(e)}")
        return None

def get_cases_data(incident_data):
    """获取与事件相关的案例数据，最多返回3条新闻内容"""
    cases_data = {}
    count = 0
    if incident_data and 'case_ids' in incident_data:
        for risk_id in incident_data['case_ids']:
            if count >= 3:  # 如果已经读取了3条新闻，就停止
                break
            try:
                response = requests.get(f"http://10.101.171.106:9000/risks/{risk_id}")
                case = response.json()
                cases_data[risk_id] = {
                    'title': case.get('title', ''),
                    'description': case.get('description', '')
                }
                count += 1
            except Exception as e:
                print(f"获取案例数据时发生错误: {str(e)}")
                continue
    return cases_data

def process_incident(incident_id, client, ontology_prompt, ontology_prompt_2):
    """处理单个事件的主函数"""
    print(f"\n处理事件 ID: {incident_id}")
    
    # 获取事件和案例数据
    incident_data = get_incident_data(incident_id)
    if not incident_data:
        print(f"未找到事件 ID: {incident_id}")
        return
    
    cases_data = get_cases_data(incident_data)
    if not cases_data:
        print(f"未找到事件 ID: {incident_id} 相关的案例")
        return


    # 读取TTL样例
    with open('TTL_example.md', 'r', encoding='utf-8') as file:
        ttl_example = file.read()

    # 第一次对话 - 生成初始TTL
    print("=" * 20 + "第一次对话 - 生成知识json" + "=" * 20 + "\n")
    entity_content = ""
    is_answering = False

    try:
        completion = client.chat.completions.create(
            model="qwen-plus-latest",
            messages=[
                {'role': 'system', 'content': ontology_prompt},
                {'role': 'user', 'content': json.dumps({
                    'cases_data': cases_data,
                    'ttl_example': ttl_example
                }, ensure_ascii=False)}],
            extra_body={"enable_thinking": False},
            stream=True,
        )

        for chunk in completion:
            if not chunk.choices:
                print("\nUsage:")
                print(chunk.usage)
                continue

            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                if not is_answering:
                    is_answering = True
                entity_content += delta.content

        # 获取当前日期
        execution_date = datetime.now().strftime("%Y-%m-%d")
        # 确保ttl-example文件夹存在
        ttl_dir = "aiid"
        if not os.path.exists(ttl_dir):
            os.makedirs(ttl_dir)

        # 生成文件名并清理
        base_name = f"ontology-incident_{incident_id}-{execution_date}"

        # 清理markdown代码块标记
        entity_content = entity_content.strip()
        if entity_content.startswith("```json"):
            entity_content = entity_content[7:]
        elif entity_content.startswith("```js"):
            entity_content = entity_content[5:]
        if entity_content.endswith("```"):
            entity_content = entity_content[:-3]
        elif entity_content.endswith("'''"):
            entity_content = entity_content[:-3]
        entity_content = entity_content.strip()
        conversation_data = json.loads(entity_content)

        # 保存初始TTL文件
        initial_file_name = f"entity_incident_{incident_id}.json"
        initial_file_name = os.path.join(ttl_dir, initial_file_name)
        with open(initial_file_name, 'w', encoding='utf-8') as file:
            json.dump(conversation_data, file, ensure_ascii=False, indent=2)
        print(f"\nJSON文件已保存为: {initial_file_name}")

        # 第二次对话 - 修改TTL
        print("=" * 20 + "第二次对话 - 生成TTL" + "=" * 20 + "\n")
        ttl_revise = ""
        is_answering = False

        completion_revise = client.chat.completions.create(
            model="qwen-plus-latest",
            messages=[
                {'role': 'system', 'content': ontology_prompt_2},
                {'role': 'user', 'content': json.dumps({
                    'entity_content': conversation_data,
                    'ttl_example': ttl_example
                }, ensure_ascii=False)}
            ],
            extra_body={"enable_thinking": True},
            stream=True,
        )

        for chunk in completion_revise:
            if not chunk.choices:
                print("\nUsage:")
                print(chunk.usage)
                continue

            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                if not is_answering:
                    is_answering = True
                ttl_revise += delta.content

        # 生成修改后的文件名
        revise_file_name = clean_filename(f"{base_name}.ttl")
        revise_file_name = os.path.join(ttl_dir, revise_file_name)

        # 清理markdown代码块标记
        ttl_revise = ttl_revise.strip()
        if ttl_revise.startswith("```ttl"):
            ttl_revise = ttl_revise[6:]
        elif ttl_revise.startswith("'''turtle"):
            ttl_revise = ttl_revise[9:]
        if ttl_revise.endswith("```"):
            ttl_revise = ttl_revise[:-3]
        elif ttl_revise.endswith("'''"):
            ttl_revise = ttl_revise[:-3]
        ttl_revise = ttl_revise.strip()

        with open(revise_file_name, 'w', encoding='utf-8') as file:
            file.write(ttl_revise)

        print(f"\n修改后的TTL文件已保存为: {revise_file_name}")

        # 生成修改后的图谱
        visualize_ttl_file(revise_file_name)

        # 第三次对话 - 生成风险分类
        print("=" * 20 + "第三次对话 - 生成风险分类" + "=" * 20 + "\n")
        
        # 读取风险分类提示词
        with open('risk_taxonomy_prompt.md', 'r', encoding='utf-8') as file:
            risk_taxonomy_prompt = file.read()

        # 进行非流式对话
        completion_risk = client.chat.completions.create(
            model="qwen-plus-latest",
            messages=[
                {'role': 'system', 'content': risk_taxonomy_prompt},
                {'role': 'user', 'content': json.dumps(conversation_data, ensure_ascii=False)}
            ],
            extra_body={"enable_thinking": False},
            stream=False,
        )

        # 获取响应内容
        risk_content = completion_risk.choices[0].message.content

        # 清理markdown代码块标记
        risk_content = risk_content.strip()
        if risk_content.startswith("```json"):
            risk_content = risk_content[7:]
        elif risk_content.startswith("```js"):
            risk_content = risk_content[5:]
        if risk_content.endswith("```"):
            risk_content = risk_content[:-3]
        elif risk_content.endswith("'''"):
            risk_content = risk_content[:-3]
        risk_content = risk_content.strip()

        # 解析JSON内容
        risk_data = json.loads(risk_content)

        # 生成风险分类文件名
        risk_file_name = f"risk_incident_{incident_id}.json"
        risk_file_name = os.path.join(ttl_dir, risk_file_name)

        # 保存风险分类JSON文件
        with open(risk_file_name, 'w', encoding='utf-8') as file:
            json.dump(risk_data, file, ensure_ascii=False, indent=2)

        print(f"\n风险分类JSON文件已保存为: {risk_file_name}")

    except Exception as e:
        print(f"处理事件 ID: {incident_id} 时发生错误: {str(e)}")

def ttl_taxonomy_generation(incident_ids):
    """
    主函数，处理一个或多个事件ID
    
    Args:
        incident_ids (str or list): 单个事件ID或事件ID列表
    """
    # 读取提示文件
    with open('entity_identification_prompt.md', 'r', encoding='utf-8') as file:
        ontology_prompt = file.read()
    
    with open('ontology_prompt_new.md', 'r', encoding='utf-8') as file:
        ontology_prompt_2 = file.read()

    # 初始化OpenAI客户端
    client = OpenAI(
        api_key='sk-71281d857bac486d82fd5a5c9b14f598',
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 将单个事件ID转换为列表
    if isinstance(incident_ids, str):
        incident_ids = [incident_ids]

    # 处理每个事件ID
    for incident_id in incident_ids:
        try:
            print(f"\n开始处理事件 ID: {incident_id}")
            process_incident(incident_id, client, ontology_prompt, ontology_prompt_2)
            print(f"完成处理事件 ID: {incident_id}")
        except Exception as e:
            print(f"处理事件 ID: {incident_id} 时发生错误: {str(e)}")
            continue

if __name__ == "__main__":
    # 示例：处理多个事件
    incident_ids = [
        "fd878abb-d962-4594-a0b0-bef275886f8a",
        # 在这里添加更多的事件ID
    ]
    ttl_taxonomy_generation(incident_ids)