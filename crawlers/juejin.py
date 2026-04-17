"""
信息聚合系统 - 掘金爬虫
爬取掘金热门技术文章，并深入爬取详情页获取完整内容
"""
import hashlib
import json
import re
from datetime import datetime

from .base import BaseCrawler


class JuejinCrawler(BaseCrawler):
    """
    掘金爬虫
    通过掘金API和网页端获取热门技术文章
    爬取频率：每2小时一次
    """

    RECOMMEND_API = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"
    DETAIL_API = "https://api.juejin.cn/content_api/v1/article/detail"
    HOME_URL = "https://juejin.cn/"

    def __init__(self):
        super().__init__("juejin", "掘金")

    def crawl(self) -> list:
        results = []
        try:
            results = self._crawl_api()
            if results:
                return results
        except Exception:
            pass

        try:
            results = self._crawl_web_page()
            if results:
                return results
        except Exception as e:
            self.logger.error(f"掘金爬取异常: {e}")
        return results

    def _crawl_api(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://juejin.cn/"
        headers["Content-Type"] = "application/json"
        payload = json.dumps({"id_type": 2, "sort_type": 200, "cursor": "0", "limit": 20})
        response = self.session.post(
            self.RECOMMEND_API,
            data=payload,
            headers=headers,
            timeout=15,
        )
        data = response.json()
        articles = data.get("data", [])
        results = []
        for article in articles[:20]:
            article_info = article.get("article_info", {})
            title = article_info.get("title", "").strip()
            if not title:
                continue
            article_id = article_info.get("article_id", "")
            source_id = hashlib.md5(f"juejin_{article_id}".encode()).hexdigest()[:16]
            brief = article_info.get("brief_content", title)[:500]
            results.append({
                "source_id": source_id,
                "title": title[:40],
                "content": brief,
                "source_url": f"https://juejin.cn/post/{article_id}",
                "event_time": datetime.now(),
                "core_entity": title[:20],
                "location": "",
                "indicator_name": "",
                "indicator_value": "",
            })
        return results

    def _crawl_web_page(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://juejin.cn/"
        response = self.fetch(self.HOME_URL, headers=headers)
        html = response.text
        results = []
        post_pattern = re.findall(r'href="/post/(\d+)"[^>]*>([^<]{4,}?)</a>', html, re.DOTALL)
        if not post_pattern:
            post_pattern = re.findall(r'/post/(\d+)[^>]*title="([^"]+)"', html, re.DOTALL)
        seen = set()
        for article_id, title in post_pattern[:20]:
            title = title.strip()
            if not title or article_id in seen:
                continue
            seen.add(article_id)
            source_id = hashlib.md5(f"juejin_{article_id}".encode()).hexdigest()[:16]
            results.append({
                "source_id": source_id,
                "title": title[:40],
                "content": title[:500],
                "source_url": f"https://juejin.cn/post/{article_id}",
                "event_time": datetime.now(),
                "core_entity": title[:20],
                "location": "",
                "indicator_name": "",
                "indicator_value": "",
            })
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://juejin.cn/"
            headers["Content-Type"] = "application/json"

            try:
                article_id = source_url.split("/post/")[-1].rstrip("/")
                payload = json.dumps({"article_id": article_id})
                response = self.session.post(
                    self.DETAIL_API,
                    data=payload,
                    headers=headers,
                    timeout=15,
                )
                data = response.json()
                article_data = data.get("data", {}).get("article_info", {})
                mark_content = article_data.get("mark_content", "")
                if mark_content:
                    mark_content = re.sub(r'```[\s\S]*?```', '', mark_content)
                    mark_content = re.sub(r'[#*`>\-\[\]()!|]', '', mark_content)
                    mark_content = re.sub(r'\s+', ' ', mark_content).strip()
                    if len(mark_content) >= 50:
                        return mark_content[:500]
                content = article_data.get("content", "")
                if content:
                    content = re.sub(r'<[^>]+>', '', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                    if len(content) >= 50:
                        return content[:500]
            except Exception:
                pass

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                text = self._extract_text_from_html(html)
                if len(text) >= 50:
                    return text[:500]
            except Exception:
                pass

            return ""
        except Exception as e:
            self.logger.warning(f"掘金详情爬取失败: {e}")
            return ""
