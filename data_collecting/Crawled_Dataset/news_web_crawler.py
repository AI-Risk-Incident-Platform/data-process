#这个文件是新闻网站爬虫的主程序

import importlib
import time as tm
import sys
from datetime import datetime
from crawler_utils import (
    load_config, clean_old_files, save_results, 
    upload_results, logging
)

def crawl_site(site_name, url, keywords, crawler_function, max_pages):
    """爬取单个网站"""
    site_results = []
    site_other_results = []
    
    for keyword in keywords:
        if not keyword:
            continue
        tm.sleep(5)  # 关键词搜索间隔
        result, other_result = crawler_function(url, keyword, max_pages)
        site_results.extend(result)
        site_other_results.extend(other_result)
    
    return site_results, site_other_results

def crawl_news(test_mode=False, test_site=None, auto_upload=True):
    """执行爬虫任务"""
    config = load_config()
    start_time = datetime.now()
    
    try:
        # 清理旧文件
        clean_old_files()
        
        sites = config.options('NewsSites')
        if test_mode and test_site:
            sites = [test_site]
            logging.info(f"测试模式: 仅爬取 {test_site}")
            
        for site_name in sites:
            if site_name.startswith('#'):
                continue
                
            url = config.get('NewsSites', site_name)
            keywords = config.get('Keywords', f'{site_name}_keywords', fallback='').split(',')
            crawler_path = config.get('CrawlerMapping', site_name)
            max_pages = int(config.get('MaxPages', f'{site_name}_max_pages', fallback=5))
            
            # 导入爬虫函数
            module_path, function_name = crawler_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            crawler_function = getattr(module, function_name)
            
            # 执行爬取
            logging.info(f"开始爬取: {site_name}")
            results, other_results = crawl_site(
                site_name, url, keywords, crawler_function, max_pages
            )
            
            # 保存结果
            aigc_file, all_file = save_results(results, other_results, site_name)
            
            # 如果需要，立即上传结果
            if auto_upload:
                upload_results(site_name, aigc_file, all_file)
            
        duration = datetime.now() - start_time
        logging.info(f"爬虫任务完成，耗时: {duration}")
        return True
        
    except Exception as e:
        logging.error(f"爬虫任务执行失败: {e}")
        return False

def main():
    """主函数：处理不同的运行模式"""
    config = load_config()
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            # 测试模式
            if not config.getboolean('TestMode', 'enabled', fallback=False):
                logging.error("测试模式未启用，请在配置文件中设置 [TestMode] enabled = True")
                return
                
            test_site = config.get('TestMode', 'test_site', fallback='')
            if not test_site:
                logging.error("测试模式需要在配置文件中指定test_site")
                return
                
            # 测试模式下检查是否自动上传
            auto_upload = config.getboolean('TestMode', 'auto_upload', fallback=True)
            crawl_news(test_mode=True, test_site=test_site, auto_upload=auto_upload)
            return
            
        elif sys.argv[1] == '--auto':
            # 自动模式
            from auto_crawler import AutoCrawler
            auto_crawler = AutoCrawler()
            if auto_crawler.auto_enabled:
                auto_crawler.run()  # 自动模式下始终上传
            else:
                logging.info("自动化功能未启用，请在配置文件中设置 [AutoCrawler] enabled = True")
            return
    
    # 检查是否为测试模式
    if config.getboolean('TestMode', 'enabled', fallback=False):
        test_site = config.get('TestMode', 'test_site', fallback='')
        if test_site:
            # 测试模式下检查是否自动上传
            auto_upload = config.getboolean('TestMode', 'auto_upload', fallback=True)
            crawl_news(test_mode=True, test_site=test_site, auto_upload=auto_upload)
        else:
            logging.error("测试模式需要在配置文件中指定test_site")
    else:
        # 手动模式下检查是否自动上传
        auto_upload = config.getboolean('Manual', 'auto_upload', fallback=True)
        crawl_news(auto_upload=auto_upload)

if __name__ == "__main__":
    main()