#这个文件定义了一个函数，用于统一处理日期时间字符串的格式转换
#它尝试多种日期时间格式，并使用dateutil库作为最后的手段

from datetime import datetime
from dateutil.parser import parse
# time_str = "2024年12月8日 13:04"
# try:
#     # 使用dateutil解析日期时间
#     date_obj = parser.parse(time_str)
#     # 格式化日期为指定格式
#     new_time_str = date_obj.strftime("%Y-%m-%d")
#     print(new_time_str)
# except ValueError:
#     print("时间格式不符合要求")
def convert_date_format(date_str):
    """
    将输入的日期时间字符串转换为指定的日期格式（年-月-日）字符串

    参数:
    date_str (str): 输入的日期时间字符串，格式需符合 '%Y-%m-%d %H:%M:%S'

    返回:
    str: 转换后的日期格式字符串，格式为 '%Y-%m-%d'
    """
    try_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y年%m月%d日 %H:%M',
        '%Y年%m月%d日%H:%M'
    ]
    for fmt in try_formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    # 如果所有格式都试过了，还是失败，就用dateutil
    try:
        date_obj = parse(date_str)
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        print("时间格式不符合要求")
        return date_str

# original_date_str = "2024-06-22 15:59"
# result = convert_date_format(original_date_str)
# if result:
#     print(result)
# 读取JSON文件
# with open('AIGC_results.json', 'r', encoding='utf-8') as f:
#     data_list = json.load(f)

# # 遍历列表中的每个字典元素，查找键为'time'的值并进行格式转换
# for item_dict in data_list:
#     if isinstance(item_dict, dict) and 'release_date' in item_dict:
#         item_dict['release_date'] = convert_date_format(item_dict['release_date'])

# # 将修改后的数据写回JSON文件
# with open('AIGC_results1.json', 'w', encoding='utf-8') as f:
#     json.dump(data_list, f, ensure_ascii=False, indent=4)
