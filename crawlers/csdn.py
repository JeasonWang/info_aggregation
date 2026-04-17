"""
信息聚合系统 - CSDN爬虫
爬取CSDN热门技术文章，并深入爬取详情页获取完整内容
"""
import hashlib
import re
from datetime import datetime

from .base import BaseCrawler


class CSDNCrawler(BaseCrawler):
    """
    CSDN爬虫
    通过CSDN API获取热门技术文章
    爬取频率：每2小时一次
    """

    HOT_API = "https://blog.csdn.net/api-user/feed/hot_article"
    ARTICLE_API = "https://blog.csdn.net/community/home-api/v1/get-business-list?page=1&size=5&businessType=blog"

    def __init__(self):
        super().__init__("csdn", "CSDN")

    def crawl(self) -> list:
        """
        爬取CSDN热门文章
        返回: 标准化信息列表
        """
        results = []
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://blog.csdn.net/"
            data = self.fetch_json(self.HOT_API, headers=headers)
            articles = data.get("data", [])
            for article in articles[:20]:
                title = article.get("title", "").strip()
                if not title:
                    continue
                article_id = article.get("article_id", "")
                source_id = hashlib.md5(f"csdn_{article_id}".encode()).hexdigest()[:16]
                desc = article.get("desc", title)[:500]
                results.append({
                    "source_id": source_id,
                    "title": title[:40],
                    "content": desc,
                    "source_url": f"https://blog.csdn.net/article/details/{article_id}",
                    "event_time": datetime.now(),
                    "core_entity": title[:20],
                    "location": "",
                    "indicator_name": "",
                    "indicator_value": "",
                })
        except Exception as e:
            self.logger.error(f"CSDN爬取异常: {e}")
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """
        爬取CSDN文章详情页，获取完整内容
        参数:
            source_url: 文章URL
            item: 基础信息字典
        返回: 完整内容文本
        """
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://blog.csdn.net/"

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                match = re.search(r'article_content[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1)
                    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    content = re.sub(r'<[^>]+>', '', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                    if len(content) >= 100:
                        return content[:500]
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
            self.logger.warning(f"CSDN详情爬取失败: {e}")
            return ""
