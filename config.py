"""
信息聚合系统 - 全局配置文件
定义系统运行所需的所有配置项，包括数据库、爬虫、定时任务等
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv("DATA_DIR", BASE_DIR)

# ==================== 数据库配置 ====================
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "info_aggregation")

if DB_TYPE == "sqlite":
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'info_aggregation.db')}"
else:
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?charset=utf8mb4"
    )

# ==================== 爬虫通用配置 ====================
CRAWLER_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

CRAWLER_REQUEST_TIMEOUT = 15
CRAWLER_RETRY_TIMES = 3
CRAWLER_RETRY_INTERVAL = 300

# ==================== 定时任务配置 ====================
#热点事件爬取
SCHEDULER_HOT_INTERVAL = 10
#经济数据爬取
SCHEDULER_ECONOMY_INTERVAL = 30
#国际大事爬取
SCHEDULER_INTERNATIONAL_INTERVAL = 30
#科技动向爬取
SCHEDULER_TECH_INTERVAL = 30
#AI大模型动向爬取
SCHEDULER_AI_INTERVAL = 30

# ==================== 日志配置 ====================
LOG_DIR = os.getenv("LOG_DIR", os.path.join(DATA_DIR, "logs"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ==================== API配置 ====================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ==================== 信息分类枚举 ====================
CATEGORY_HOT = "热点事件"
CATEGORY_ECONOMY = "经济数据"
CATEGORY_INTERNATIONAL = "国际大事"
CATEGORY_TECH = "科技动向"
CATEGORY_AI = "AI大模型动向"

CATEGORIES = [
    CATEGORY_HOT,
    CATEGORY_ECONOMY,
    CATEGORY_INTERNATIONAL,
    CATEGORY_TECH,
    CATEGORY_AI,
]

# ==================== 渠道配置 ====================
CHANNELS = [
    {"name": "微博", "code": "weibo", "category": CATEGORY_HOT},
    {"name": "今日头条", "code": "toutiao", "category": CATEGORY_HOT},
    {"name": "小红书", "code": "xiaohongshu", "category": CATEGORY_HOT},
    {"name": "东方财富网", "code": "eastmoney", "category": CATEGORY_ECONOMY},
    {"name": "路透社", "code": "reuters", "category": CATEGORY_INTERNATIONAL},
    {"name": "CSDN", "code": "csdn", "category": CATEGORY_TECH},
    {"name": "掘金", "code": "juejin", "category": CATEGORY_TECH},
    {"name": "博客园", "code": "cnblogs", "category": CATEGORY_TECH},
    {"name": "36氪", "code": "36kr", "category": CATEGORY_AI},
    {"name": "知乎", "code": "zhihu", "category": CATEGORY_AI},
]
