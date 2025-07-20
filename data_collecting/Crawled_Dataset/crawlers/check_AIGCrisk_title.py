#检查新闻标题用以判断是否与AIGC风险相关
#该代码调用了一个API来判断新闻标题是否与AIGC风险相关

import requests
def check_AIGCrisk_news(speak):
# """
# 调用服务器的千问模型,如果是接口调用请修改接口，如果是本地调用请修改为本地模型的调用方式 更改ip和api

# :param speak:新闻标题
# :return: 是否与AIGC风险相关的布尔类型
# """
    data = {
    "prompt": "你是一名AIGC风险治理专家，现在需要根据我给出的新闻标题来判断其是否与AIGC风险相关。AIGC风险是指在使用人工智能技术自动生成内容的过程中可能遇到的各种问题和挑战，这些问题包括但不限于数据隐私泄露、数据来源合法性问题、内容生成的合规性问题、数据跨境传输风险、算法偏见、内容的准确性和适当性问题、以及可能的法律和伦理风险。这些风险通常与AI系统的设计、部署和使用方式直接相关。请你阅读我给出的新闻标题，再仔细思考什么是AIGC风险，并做出判断：如果相关就在最后返回“AIGCrisk_relevant”字符串，如果不相关就在最后返回“AIGCrisk_Irrelevant”",
    "input": speak
    }

    # 发送POST请求到指定的API·  待修改
    response = requests.post("target_ip/target_api", json=data)


    print(response.json())
    
    # 获取内容并打印
    content = response.json()['response']
    # content = response.json()
    # if response.json()=={}:
    #     print("1")
    # print(content)
    if "AIGCrisk_relevant" in content:
        return True
    else: 
        return False
# speak="知名医学专家“被带货”，经济日报：重视防范AI造假风险"
# print(check_AIGCrisk_news(speak))