"""
信息聚合系统 - 主入口
启动FastAPI服务、初始化数据库、注册爬虫、启动定时任务
"""
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import LOG_DIR, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT, API_HOST, API_PORT


def setup_logging():
    """配置日志系统：控制台输出 + 文件输出"""
    os.makedirs(LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        os.path.join(LOG_DIR, "info_aggregation.log"),
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    root_logger.addHandler(file_handler)


def register_all_crawlers():
    """注册所有渠道爬虫到注册中心"""
    from crawlers.registry import crawler_registry
    from crawlers.weibo import WeiboCrawler
    from crawlers.toutiao import ToutiaoCrawler
    from crawlers.xiaohongshu import XiaohongshuCrawler
    from crawlers.eastmoney import EastmoneyCrawler
    from crawlers.reuters import ReutersCrawler
    from crawlers.csdn import CSDNCrawler
    from crawlers.juejin import JuejinCrawler
    from crawlers.cnblogs import CnblogsCrawler
    from crawlers.kr36 import Kr36Crawler
    from crawlers.zhihu import ZhihuCrawler

    crawlers = [
        WeiboCrawler(),
        ToutiaoCrawler(),
        XiaohongshuCrawler(),
        EastmoneyCrawler(),
        ReutersCrawler(),
        CSDNCrawler(),
        JuejinCrawler(),
        CnblogsCrawler(),
        Kr36Crawler(),
        ZhihuCrawler(),
    ]

    for crawler in crawlers:
        crawler_registry.register(crawler.channel_code, crawler)

    logging.getLogger(__name__).info(f"已注册{len(crawlers)}个爬虫")


def main():
    """系统主入口"""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("信息聚合系统 Info_aggregation 启动中...")
    logger.info("=" * 60)

    # 1. 初始化数据库和模拟数据
    logger.info("[1/4] 初始化数据库和模拟数据...")
    from sql.init_data import init_all_data
    init_all_data()

    # 2. 注册所有爬虫
    logger.info("[2/4] 注册爬虫模块...")
    register_all_crawlers()

    # 3. 启动定时任务
    logger.info("[3/4] 启动定时任务调度器...")
    from scheduler import setup_scheduler
    scheduler = setup_scheduler()
    scheduler.start()

    # 4. 启动FastAPI服务
    logger.info("[4/4] 启动API服务...")
    import uvicorn
    from api import app

    logger.info(f"API服务启动于 http://{API_HOST}:{API_PORT}")
    logger.info(f"API文档地址 http://{API_HOST}:{API_PORT}/docs")
    uvicorn.run(app, host=API_HOST, port=API_PORT, log_level="info")


if __name__ == "__main__":
    main()
