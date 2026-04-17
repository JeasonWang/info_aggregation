"""
信息聚合系统 - 今日头条爬虫
爬取今日头条热点新闻，并深入爬取详情页获取完整内容
"""
import hashlib
import re
from datetime import datetime

from .base import BaseCrawler


class ToutiaoCrawler(BaseCrawler):
    """
    今日头条爬虫
    通过头条热点API获取热点新闻
    爬取频率：每30分钟一次
    """

    TREND_API = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
    DETAIL_API = "https://www.toutiao.com/article/{item_id}/"

    def __init__(self):
        super().__init__("toutiao", "今日头条")

    def crawl(self) -> list:
        """
        爬取今日头条热点
        返回: 标准化信息列表
        """
        results = []
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.toutiao.com/"
            data = self.fetch_json(self.TREND_API, headers=headers)
            items = data.get("data", [])
            for item in items[:20]:
                title = item.get("Title", "").strip()
                if not title:
                    continue
                cluster_id = item.get("ClusterId", "")
                source_id = hashlib.md5(f"toutiao_{cluster_id}".encode()).hexdigest()[:16]
                results.append({
                    "source_id": source_id,
                    "title": title[:40],
                    "content": item.get("Title", "")[:500],
                    "source_url": f"https://www.toutiao.com/trending/{cluster_id}/",
                    "event_time": datetime.now(),
                    "core_entity": title[:20],
                    "location": "",
                    "indicator_name": "",
                    "indicator_value": "",
                })
        except Exception as e:
            self.logger.error(f"头条爬取异常: {e}")
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """
        爬取头条文章详情页，获取完整内容
        参数:
            source_url: 文章URL
            item: 基础信息字典
        返回: 完整内容文本
        """
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.toutiao.com/"
            headers["Accept"] = "application/json, text/plain, */*"

            try:
                trend_detail_api = f"https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
                data = self.fetch_json(trend_detail_api, headers=headers)
                items = data.get("data", [])
                title = item.get("title", "")
                for trend_item in items:
                    if title in trend_item.get("Title", ""):
                        cluster_id = trend_item.get("ClusterId", "")
                        detail_api = f"https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc&cluster_id={cluster_id}"
                        detail_data = self.fetch_json(detail_api, headers=headers)
                        articles = detail_data.get("data", [])
                        if articles:
                            first = articles[0]
                            content = first.get("Abstract", "")
                            if content and len(content) >= 100:
                                return content[:500]
                            content = first.get("Content", "")
                            if content:
                                content = re.sub(r'<[^>]+>', '', content)
                                content = re.sub(r'\s+', ' ', content).strip()
                                if len(content) >= 100:
                                    return content[:500]
                        break
            except Exception:
                pass

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                text = self._extract_text_from_html(html)
                if len(text) >= 100:
                    return text[:500]
            except Exception:
                pass

            return ""
        except Exception as e:
            self.logger.warning(f"头条详情爬取失败: {e}")
            return ""
