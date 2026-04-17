"""
信息聚合系统 - 36氪爬虫
爬取36氪AI/大模型相关资讯，并深入爬取详情页获取完整内容
"""
import hashlib
import re
from datetime import datetime

from .base import BaseCrawler


class Kr36Crawler(BaseCrawler):
    """
    36氪爬虫
    通过36氪API获取AI/大模型相关资讯
    爬取频率：每2小时一次
    """

    HOT_API = "https://36kr.com/api/search-column/mainsite?per_page=20&page=1"
    DETAIL_API = "https://36kr.com/p/{article_id}.html"

    def __init__(self):
        super().__init__("36kr", "36氪")

    def crawl(self) -> list:
        """
        爬取36氪热门资讯
        返回: 标准化信息列表
        """
        results = []
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://36kr.com/"
            data = self.fetch_json(self.HOT_API, headers=headers)
            items = data.get("data", {}).get("items", [])
            for item in items[:20]:
                entity = item.get("entity", {})
                title = entity.get("title", "").strip()
                if not title:
                    continue
                article_id = entity.get("id", "")
                source_id = hashlib.md5(f"36kr_{article_id}".encode()).hexdigest()[:16]
                summary = entity.get("summary", title)[:500]
                results.append({
                    "source_id": source_id,
                    "title": title[:40],
                    "content": summary,
                    "source_url": f"https://36kr.com/p/{article_id}",
                    "event_time": datetime.now(),
                    "core_entity": title[:20],
                    "location": "",
                    "indicator_name": "",
                    "indicator_value": "",
                })
        except Exception as e:
            self.logger.error(f"36氪爬取异常: {e}")
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """
        爬取36氪文章详情页，获取完整内容
        参数:
            source_url: 文章URL
            item: 基础信息字典
        返回: 完整内容文本
        """
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://36kr.com/"

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                match = re.search(r'window\.initialState\s*=\s*({.*?})\s*;?\s*</script>', html, re.DOTALL)
                if match:
                    import json
                    json_str = match.group(1)
                    json_str = re.sub(r':undefined', ':null', json_str)
                    state = json.loads(json_str)
                    article_detail = state.get("articleDetail", {})
                    article_data = article_detail.get("articleDetailData", {}).get("data", {})
                    content = article_data.get("content", "")
                    if content:
                        content = re.sub(r'<[^>]+>', '', content)
                        content = re.sub(r'\s+', ' ', content).strip()
                        if len(content) >= 100:
                            return content[:500]
            except Exception:
                pass

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                match = re.search(r'class="article-content"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL | re.IGNORECASE)
                if not match:
                    match = re.search(r'class="content"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
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
            self.logger.warning(f"36氪详情爬取失败: {e}")
            return ""
