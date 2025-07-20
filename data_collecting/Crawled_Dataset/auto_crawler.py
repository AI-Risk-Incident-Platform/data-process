#这个文件定义了自动化爬虫的功能
#它使用schedule库来定时执行爬虫任务

import schedule
import time
from crawler_utils import load_config, logging

class AutoCrawler:
    def __init__(self):
        self.config = load_config()
        self._init_settings()

    def _init_settings(self):
        """初始化设置"""
        self.auto_enabled = self.config.getboolean('AutoCrawler', 'enabled', fallback=False)
        self.schedule_time = self.config.get('AutoCrawler', 'schedule_time', fallback='02:00').strip()
        self.schedule_day = self.config.get('AutoCrawler', 'schedule_day', fallback='monday').strip()

    def execute_task(self):
        """执行定时任务"""
        try:
            # 自动模式下始终上传结果
            from main import crawl_news
            crawl_news(auto_upload=True)
        except Exception as e:
            logging.error(f"执行任务失败: {e}")

    def run(self):
        """运行自动化程序"""
        if not self.auto_enabled:
            logging.info("自动化功能未启用")
            return

        logging.info(f"自动化爬虫已启动，将在每周{self.schedule_day}的{self.schedule_time}执行")
        
        # 设置定时任务
        getattr(schedule.every(), self.schedule_day).at(self.schedule_time).do(self.execute_task)

        # 运行调度器
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    auto_crawler = AutoCrawler()
    if auto_crawler.auto_enabled:
        auto_crawler.run()  # 启动定时任务
    else:
        logging.info("自动化功能未启用，如需启用请在config.ini中设置enabled=true")

if __name__ == "__main__":
    main() 