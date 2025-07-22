# -*- coding: utf-8 -*-

import os
from openai import OpenAI
import json
from datetime import datetime
# from ttl_visualization import visualize_ttl_file
import re
import time
import requests
import logging
from pathlib import Path
import argparse
import math
from concurrent.futures import ProcessPoolExecutor

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

def setup_logging(process_id=None):
    """
    设置日志记录
    
    Args:
        process_id (int, optional): 进程ID，用于区分不同进程的日志
        
    Returns:
        str: 日志文件路径
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 根据是否有进程ID来生成不同的日志文件名
    if process_id is not None:
        log_file = os.path.join(log_dir, f"process_{process_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    else:
        log_file = os.path.join(log_dir, f"processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # 创建新的日志处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    console_handler = logging.StreamHandler()
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 获取根日志记录器并设置
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 添加新的处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return log_file

def get_incident_data(incident_id):
    """从本地JSONL文件获取指定incident_id的事件数据"""
    try:
        with open('case-test/new_incidents.jsonl', 'r', encoding='utf-8') as file:
            for line in file:
                incident = json.loads(line)
                if str(incident['incident_id']) == str(incident_id):
                    return incident
        logging.warning(f"未找到事件 ID: {incident_id}")
        return None
    except Exception as e:
        logging.error(f"获取事件数据时发生错误: {str(e)}")
        return None

def get_cases_data(incident_data):
    """从本地JSONL文件获取与事件相关的案例数据，最多返回3条新闻内容"""
    cases_data = {}
    count = 0
    if incident_data and 'ids' in incident_data:
        try:
            with open('case-test/new_cases.jsonl', 'r', encoding='utf-8') as file:
                for line in file:
                    case = json.loads(line)
                    if case.get('id') in incident_data['ids']:
                        cases_data[str(case['id'])] = {
                            'title': case.get('title', ''),
                            'description': case.get('description', '')
                        }
                        count += 1
                        if count >= 3:  # 如果已经读取了3条新闻，就停止
                            break
            if not cases_data:
                logging.warning(f"未找到事件相关的案例数据")
        except Exception as e:
            logging.error(f"获取案例数据时发生错误: {str(e)}")
    return cases_data

def process_incident(incident_id, client, ontology_prompt, ontology_prompt_2):
    """处理单个事件的主函数"""
    logging.info(f"开始处理事件 ID: {incident_id}")
    
    # 获取事件和案例数据
    incident_data = get_incident_data(incident_id)
    if not incident_data:
        logging.error(f"未找到事件 ID: {incident_id}")
        return
    
    cases_data = get_cases_data(incident_data)
    if not cases_data:
        logging.error(f"未找到事件 ID: {incident_id} 相关的案例")
        return

    # 读取TTL样例
    try:
        with open('TTL_example.md', 'r', encoding='utf-8') as file:
            ttl_example = file.read()
    except Exception as e:
        logging.error(f"读取TTL样例文件失败: {str(e)}")
        return

    # 创建主目录和事件子目录
    main_dir = "incidentinfo"
    incident_dir = os.path.join(main_dir, f"incident_{incident_id}")
    if not os.path.exists(main_dir):
        os.makedirs(main_dir)
    if not os.path.exists(incident_dir):
        os.makedirs(incident_dir)

    try:
        # 第一次对话 - 生成初始TTL
        logging.info(f"事件 {incident_id} - 开始第一次对话生成知识json")
        
        completion = client.chat.completions.create(
            model="deepseek-v3-250324",
            messages=[
                {'role': 'system', 'content': ontology_prompt},
                {'role': 'user', 'content': json.dumps({
                    'cases_data': cases_data,
                    'ttl_example': ttl_example
                }, ensure_ascii=False)}],
        )

        entity_content = completion.choices[0].message.content
        logging.info(f"事件 {incident_id} - 获取到LLM响应: {entity_content[:200]}...")  # 记录响应内容的前200个字符

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
        
        logging.info(f"事件 {incident_id} - 清理后的内容: {entity_content[:200]}...")  # 记录清理后的内容

        try:
            conversation_data = json.loads(entity_content)
        except json.JSONDecodeError as e:
            logging.error(f"事件 {incident_id} - JSON解析错误: {str(e)}")
            logging.error(f"事件 {incident_id} - 尝试解析的内容: {entity_content}")
            return

        # 保存初始TTL文件
        initial_file_name = f"entity_incident_{incident_id}.json"
        initial_file_name = os.path.join(incident_dir, initial_file_name)
        with open(initial_file_name, 'w', encoding='utf-8') as file:
            json.dump(conversation_data, file, ensure_ascii=False, indent=2)
        logging.info(f"事件 {incident_id} - 成功保存初始JSON文件: {initial_file_name}")

        # 第二次对话 - 生成TTL
        logging.info(f"事件 {incident_id} - 开始第二次对话生成TTL")
        
        completion_second = client.chat.completions.create(
            model="doubao-1-5-pro-32k-250115",
            messages=[
                {'role': 'system', 'content': ontology_prompt_2},
                {'role': 'user', 'content': json.dumps({
                    'entity_content': conversation_data,
                    'ttl_example': ttl_example
                }, ensure_ascii=False)}
            ],
        )
        ttl_revise = completion_second.choices[0].message.content
        logging.info(f"事件 {incident_id} - 获取到第二次LLM响应: {ttl_revise[:200]}...")  # 记录响应内容

        # 生成修改后的文件名
        base_name = f"ontology_incident_{incident_id}"
        revise_file_name = clean_filename(f"{base_name}.ttl")
        revise_file_name = os.path.join(incident_dir, revise_file_name)

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

        logging.info(f"事件 {incident_id} - 成功保存TTL文件: {revise_file_name}")

        # 第三次对话 - 生成风险分类
        logging.info(f"事件 {incident_id} - 开始第三次对话生成风险分类")
        
        # 读取风险分类提示词
        try:
            with open('risk_taxonomy_prompt.md', 'r', encoding='utf-8') as file:
                risk_taxonomy_prompt = file.read()
        except Exception as e:
            logging.error(f"事件 {incident_id} - 读取风险分类提示词失败: {str(e)}")
            return

        completion_risk = client.chat.completions.create(
            model="doubao-1-5-pro-32k-250115",
            messages=[
                {'role': 'system', 'content': risk_taxonomy_prompt},
                {'role': 'user', 'content': json.dumps(conversation_data, ensure_ascii=False)}
            ],
        )

        risk_content = completion_risk.choices[0].message.content
        logging.info(f"事件 {incident_id} - 获取到第三次LLM响应: {risk_content[:200]}...")  # 记录响应内容

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

        try:
            # 解析JSON内容
            risk_data = json.loads(risk_content)
        except json.JSONDecodeError as e:
            logging.error(f"事件 {incident_id} - 风险分类JSON解析错误: {str(e)}")
            logging.error(f"事件 {incident_id} - 尝试解析的内容: {risk_content}")
            return

        # 生成风险分类文件名
        risk_file_name = f"risk_incident_{incident_id}.json"
        risk_file_name = os.path.join(incident_dir, risk_file_name)

        # 保存风险分类JSON文件
        with open(risk_file_name, 'w', encoding='utf-8') as file:
            json.dump(risk_data, file, ensure_ascii=False, indent=2)

        logging.info(f"事件 {incident_id} - 成功保存风险分类文件: {risk_file_name}")
        logging.info(f"事件 {incident_id} - 处理完成")

    except Exception as e:
        logging.error(f"事件 {incident_id} - 处理过程中发生错误: {str(e)}")
        logging.error(f"事件 {incident_id} - 错误详情:", exc_info=True)  # 添加完整的错误堆栈信息

def ttl_taxonomy_generation(incident_id):
    """
    主函数，处理单个事件ID
    
    Args:
        incident_id (str): 事件ID
    """
    try:
        # 读取提示文件
        with open('entity_identification_prompt.md', 'r', encoding='utf-8') as file:
            ontology_prompt = file.read()
        
        with open('ontology_prompt_new.md', 'r', encoding='utf-8') as file:
            ontology_prompt_2 = file.read()

        # 豆包火山引擎
        client = OpenAI(
            api_key="28be7d5d-b9c9-4cc8-8ac8-528aa0870790",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
        )

        process_incident(incident_id, client, ontology_prompt, ontology_prompt_2)
    except Exception as e:
        logging.error(f"事件 {incident_id} - 初始化处理失败: {str(e)}")

def split_incidents(incident_ids, num_parts=4):
    """
    将事件ID列表切分为指定数量的部分
    
    Args:
        incident_ids (list): 事件ID列表
        num_parts (int): 要切分的部分数量
        
    Returns:
        list: 包含num_parts个子列表的列表，每个子列表包含一部分事件ID
    """
    if not incident_ids:
        return []
    
    # 计算每个部分应该包含的事件数量
    total_incidents = len(incident_ids)
    incidents_per_part = math.ceil(total_incidents / num_parts)
    
    # 切分事件ID列表
    parts = []
    for i in range(0, total_incidents, incidents_per_part):
        part = incident_ids[i:i + incidents_per_part]
        if part:  # 只添加非空的部分
            parts.append(part)
    
    return parts

def process_incident_batch(incident_ids, ontology_prompt, ontology_prompt_2, process_id):
    """
    处理一批事件ID
    
    Args:
        incident_ids (list): 要处理的事件ID列表
        ontology_prompt (str): 实体识别提示词
        ontology_prompt_2 (str): 本体生成提示词
        process_id (int): 进程ID
    """
    # 为每个进程设置独立的日志
    log_file = setup_logging(process_id)
    logging.info(f"进程 {process_id} 开始处理，日志文件保存在: {log_file}")
    logging.info(f"进程 {process_id} 将处理以下事件ID: {incident_ids}")
    
    try:
        # 豆包火山引擎
        client = OpenAI(
            api_key="28be7d5d-b9c9-4cc8-8ac8-528aa0870790",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
        )

        for incident_id in incident_ids:
            try:
                logging.info(f"进程 {process_id} 开始处理事件 ID: {incident_id}")
                process_incident(incident_id, client, ontology_prompt, ontology_prompt_2)
                logging.info(f"进程 {process_id} 完成处理事件 ID: {incident_id}")
                time.sleep(1)  # 添加短暂延迟，避免请求过于频繁
            except Exception as e:
                logging.error(f"进程 {process_id} 处理事件 ID: {incident_id} 时发生错误: {str(e)}")
                continue
    except Exception as e:
        logging.error(f"进程 {process_id} 发生错误: {str(e)}")
    finally:
        logging.info(f"进程 {process_id} 处理完成")

if __name__ == "__main__":
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='处理指定的事件ID')
    parser.add_argument('--ids', nargs='+', help='要处理的事件ID列表，例如：--ids 1 2 3')
    parser.add_argument('--all', action='store_true', help='处理所有事件')
    parser.add_argument('--parallel', action='store_true', help='是否并行处理事件')
    args = parser.parse_args()

    # 设置主进程日志
    log_file = setup_logging()
    logging.info(f"主进程开始运行，日志文件保存在: {log_file}")
    
    # 读取提示文件
    try:
        with open('entity_identification_prompt.md', 'r', encoding='utf-8') as file:
            ontology_prompt = file.read()
        
        with open('ontology_prompt_new.md', 'r', encoding='utf-8') as file:
            ontology_prompt_2 = file.read()
        logging.info("成功读取提示文件")
    except Exception as e:
        logging.error(f"读取提示文件失败: {str(e)}")
        exit(1)
    
    # 获取要处理的事件ID列表
    incident_ids = []
    if args.all:
        # 处理所有事件
        try:
            with open('case-test/new_incidents.jsonl', 'r', encoding='utf-8') as file:
                for line in file:
                    incident = json.loads(line)
                    incident_ids.append(incident['incident_id'])
            logging.info(f"从文件读取到 {len(incident_ids)} 个事件ID")
        except Exception as e:
            logging.error(f"读取事件ID列表失败: {str(e)}")
            exit(1)
    elif args.ids:
        # 处理指定的ID列表
        incident_ids = args.ids
        logging.info(f"将处理指定的 {len(incident_ids)} 个事件ID")
    else:
        logging.error("请指定要处理的事件ID或使用--all参数处理所有事件")
        exit(1)

    if args.parallel:
        # 将事件ID列表切分为4个部分
        incident_parts = split_incidents(incident_ids, 4)
        logging.info(f"将事件集切分为 {len(incident_parts)} 个部分进行并行处理")
        
        # 使用进程池并行处理事件
        with ProcessPoolExecutor(max_workers=4) as executor:
            # 为每个部分创建任务，传递提示词和进程ID
            futures = [
                executor.submit(process_incident_batch, part, ontology_prompt, ontology_prompt_2, i+1)
                for i, part in enumerate(incident_parts)
            ]
            # 等待所有任务完成
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"子进程执行失败: {str(e)}")
    else:
        # 串行处理事件
        client = OpenAI(
            api_key="28be7d5d-b9c9-4cc8-8ac8-528aa0870790",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
        )
        for incident_id in incident_ids:
            logging.info(f"\n开始处理事件 ID: {incident_id}")
            try:
                process_incident(incident_id, client, ontology_prompt, ontology_prompt_2)
            except Exception as e:
                logging.error(f"处理事件 ID: {incident_id} 时发生错误: {str(e)}")
                continue
            logging.info(f"完成处理事件 ID: {incident_id}")
            time.sleep(1)  # 添加短暂延迟，避免请求过于频繁
    
    logging.info("所有事件处理完成")