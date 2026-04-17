"""
信息聚合系统 - 爬虫基类
定义爬虫接口规范，所有渠道爬虫必须继承此基类并实现crawl方法
新增渠道只需：1.继承BaseCrawler 2.实现crawl方法 3.注册到registry
"""
import random
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime

import requests

from config import CRAWLER_USER_AGENTS, CRAWLER_REQUEST_TIMEOUT, CRAWLER_RETRY_TIMES, CRAWLER_RETRY_INTERVAL


class BaseCrawler(ABC):
    """
    爬虫抽象基类
    定义了爬虫的通用行为和接口规范
    子类必须实现crawl方法，返回标准化的信息列表
    子类可选实现fetch_detail方法，用于爬取详情页获取完整内容
    """

    def __init__(self, channel_code: str, channel_name: str):
        """
        初始化爬虫
        参数:
            channel_code: 渠道编码，如 'weibo'
            channel_name: 渠道名称，如 '微博'
        """
        self.channel_code = channel_code
        self.channel_name = channel_name
        self.logger = logging.getLogger(f"crawler.{channel_code}")
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=1,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get_random_ua(self) -> str:
        """随机获取User-Agent，防止被反爬"""
        return random.choice(CRAWLER_USER_AGENTS)

    def _build_headers(self) -> dict:
        """构建请求头，包含随机User-Agent"""
        return {
            "User-Agent": self._get_random_ua(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def fetch(self, url: str, params: dict = None, headers: dict = None, timeout: int = None) -> requests.Response:
        """
        发送HTTP GET请求，内置重试机制
        参数:
            url: 请求URL
            params: 查询参数
            headers: 自定义请求头
            timeout: 超时时间(秒)，默认使用配置值
        返回:
            requests.Response对象
        异常:
            请求失败超过重试次数后抛出异常
        """
        req_headers = headers or self._build_headers()
        req_timeout = timeout or CRAWLER_REQUEST_TIMEOUT
        last_exception = None

        for attempt in range(1, CRAWLER_RETRY_TIMES + 1):
            try:
                self.logger.info(f"请求 {url} (第{attempt}次)")
                response = self.session.get(
                    url,
                    params=params,
                    headers=req_headers,
                    timeout=req_timeout,
                )
                response.raise_for_status()
                time.sleep(random.uniform(0.5, 2.0))
                return response
            except requests.Timeout as e:
                last_exception = e
                self.logger.warning(f"请求超时(第{attempt}次): {url}")
                if attempt < CRAWLER_RETRY_TIMES:
                    time.sleep(CRAWLER_RETRY_INTERVAL / 60)
            except requests.ConnectionError as e:
                last_exception = e
                self.logger.warning(f"连接失败(第{attempt}次): {url} - {e}")
                if attempt < CRAWLER_RETRY_TIMES:
                    time.sleep(CRAWLER_RETRY_INTERVAL / 60)
            except requests.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else 0
                if status_code in (401, 403, 404):
                    self.logger.warning(f"HTTP {status_code}，不重试: {url}")
                    raise
                last_exception = e
                self.logger.warning(f"HTTP错误(第{attempt}次): {status_code} - {url}")
                if attempt < CRAWLER_RETRY_TIMES:
                    time.sleep(CRAWLER_RETRY_INTERVAL / 60)
            except requests.RequestException as e:
                last_exception = e
                self.logger.warning(f"请求失败(第{attempt}次): {e}")
                if attempt < CRAWLER_RETRY_TIMES:
                    time.sleep(CRAWLER_RETRY_INTERVAL / 60)

        self.logger.error(f"请求{url}失败，已重试{CRAWLER_RETRY_TIMES}次")
        raise last_exception

    def fetch_json(self, url: str, params: dict = None, headers: dict = None, timeout: int = None) -> dict:
        """
        发送HTTP GET请求并返回JSON数据
        参数:
            url: 请求URL
            params: 查询参数
            headers: 自定义请求头
            timeout: 超时时间(秒)
        返回:
            解析后的JSON字典
        """
        response = self.fetch(url, params=params, headers=headers, timeout=timeout)
        try:
            return response.json()
        except ValueError:
            self.logger.warning(f"JSON解析失败: {url}")
            return {}

    @abstractmethod
    def crawl(self) -> list:
        """
        执行爬取（抽象方法，子类必须实现）
        返回:
            标准化的信息列表，每条信息为字典格式:
            {
                "source_id": str,       # 来源唯一标识
                "title": str,           # 标题(≤40字)
                "content": str,         # 内容/简介(≤500字)
                "source_url": str,      # 来源URL
                "event_time": datetime, # 事件时间
                "core_entity": str,     # 核心主体
                "location": str,        # 地点(可选)
                "indicator_name": str,  # 指标名称(经济类)
                "indicator_value": str, # 指标数值(经济类)
            }
        """
        raise NotImplementedError

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """
        爬取详情页获取完整内容（子类可覆盖实现）
        参数:
            source_url: 详情页URL
            item: 列表页已爬取的基础信息字典
        返回:
            详情页完整内容文本，爬取失败返回空字符串
        注意:
            子类应覆盖此方法实现各渠道的详情页解析逻辑
            基类提供默认实现：尝试请求URL并提取页面文本
        """
        if not source_url:
            return ""
        try:
            headers = self._build_headers()
            response = self.fetch(source_url, headers=headers, timeout=15)
            return self._extract_text_from_html(response.text)
        except Exception as e:
            self.logger.warning(f"详情页爬取失败 [{source_url}]: {e}")
            return ""

    def _extract_text_from_html(self, html: str) -> str:
        """
        从HTML中提取纯文本内容（通用方法）
        参数:
            html: HTML字符串
        返回:
            提取的纯文本
        """
        import re
        content_patterns = [
            r'<article[^>]*>(.*?)</article>',
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*article[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*detail[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*post[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*body[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*text[^"]*"[^>]*>(.*?)</div>',
        ]
        for pattern in content_patterns:
            match = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
            if match:
                text = match.group(1)
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<[^>]+>', '', text)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) >= 100:
                    return text
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def safe_crawl(self) -> list:
        """
        安全执行爬取，捕获异常并记录日志
        返回:
            爬取到的信息列表，异常时返回空列表
        """
        try:
            self.logger.info(f"开始爬取 {self.channel_name}({self.channel_code})")
            results = self.crawl()
            self.logger.info(f"爬取完成 {self.channel_name}: 获取{len(results)}条信息")
            return results
        except Exception as e:
            self.logger.error(f"爬取 {self.channel_name} 失败: {e}", exc_info=True)
            return []

    def safe_fetch_detail(self, source_url: str, item: dict) -> tuple:
        """
        安全执行详情页爬取，捕获异常并返回结果和状态
        参数:
            source_url: 详情页URL
            item: 列表页已爬取的基础信息字典
        返回:
            (detail_content, status, error_message) 元组
            - detail_content: 详情内容文本
            - status: "success" 或 "failed"
            - error_message: 失败原因，成功时为空字符串
        """
        if not source_url:
            return "", "failed", "详情页URL为空"
        try:
            detail = self.fetch_detail(source_url, item)
            if detail and len(detail.strip()) >= 50:
                return detail[:500], "success", ""
            else:
                return detail[:500] if detail else "", "failed", f"详情内容过短(仅{len(detail.strip()) if detail else 0}字)"
        except requests.Timeout:
            return "", "failed", "详情页请求超时"
        except requests.ConnectionError:
            return "", "failed", "详情页连接失败"
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else 0
            return "", "failed", f"详情页HTTP错误({status_code})"
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)[:200]}"
            self.logger.warning(f"详情爬取异常 [{source_url}]: {error_msg}")
            return "", "failed", error_msg
