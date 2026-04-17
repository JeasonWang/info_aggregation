"""
信息聚合系统 - 路透社爬虫
爬取路透社国际新闻，并深入爬取详情页获取完整内容
"""
import hashlib
import re
from datetime import datetime

from .base import BaseCrawler


class ReutersCrawler(BaseCrawler):
    """
    路透社爬虫
    通过路透社API获取国际新闻
    爬取频率：每2小时一次
    """

    NEWS_API = "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-section-alias-or-id-v1"
    ARTICLE_API = "https://www.reuters.com/pf/api/v3/content/fetch/article-by-id-or-url-v1"

    def __init__(self):
        super().__init__("reuters", "路透社")

    def crawl(self) -> list:
        """
        爬取路透社国际新闻
        返回: 标准化信息列表
        """
        results = []
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.reuters.com/world/"
            params = {
                "size": 20,
                "section_alias": "world",
            }
            data = self.fetch_json(self.NEWS_API, params=params, headers=headers)
            articles = data.get("result", {}).get("articles", [])
            for article in articles[:20]:
                title = article.get("title", "").strip()
                if not title:
                    continue
                article_id = article.get("id", "")
                source_id = hashlib.md5(f"reuters_{article_id}".encode()).hexdigest()[:16]
                summary = article.get("description", title)[:500]
                results.append({
                    "source_id": source_id,
                    "title": title[:40],
                    "content": summary,
                    "source_url": f"https://www.reuters.com/world/{article_id}/",
                    "event_time": datetime.now(),
                    "core_entity": title[:20],
                    "location": "",
                    "indicator_name": "",
                    "indicator_value": "",
                })
        except Exception as e:
            self.logger.error(f"路透社爬取异常: {e}")
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """
        爬取路透社文章详情页，获取完整内容
        参数:
            source_url: 文章URL
            item: 基础信息字典
        返回: 完整内容文本
        """
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.reuters.com/"

            try:
                import json
                payload = json.dumps({"url": source_url})
                post_headers = headers.copy()
                post_headers["Content-Type"] = "application/json"
                response = self.session.post(
                    self.ARTICLE_API,
                    data=payload,
                    headers=post_headers,
                    timeout=15,
                )
                data = response.json()
                article = data.get("result", {})
                content_parts = article.get("content_items", [])
                if content_parts:
                    texts = []
                    for part in content_parts:
                        if part.get("type") == "paragraph":
                            text = part.get("content", "")
                            text = re.sub(r'<[^>]+>', '', text).strip()
                            if text:
                                texts.append(text)
                    full_text = " ".join(texts)
                    if len(full_text) >= 100:
                        return full_text[:500]
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
            self.logger.warning(f"路透社详情爬取失败: {e}")
            return ""
