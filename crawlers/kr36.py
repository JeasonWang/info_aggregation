"""
信息聚合系统 - 36氪爬虫
爬取36氪AI/大模型相关热门文章，并深入爬取详情页获取完整内容
"""
import hashlib
import json
import re
from datetime import datetime

from .base import BaseCrawler


class Kr36Crawler(BaseCrawler):
    """
    36氪爬虫
    通过36氪API和网页端获取热门科技文章
    爬取频率：每2小时一次
    """

    HOT_API = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"
    DETAIL_API = "https://gateway.36kr.com/api/mis/article/detail"
    HOT_URL = "https://36kr.com/hot-list/catalog"
    AI_URL = "https://36kr.com/information/AI"

    def __init__(self):
        super().__init__("36kr", "36氪")

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
            self.logger.error(f"36氪爬取异常: {e}")
        return results

    def _crawl_api(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://36kr.com/"
        headers["Content-Type"] = "application/json"
        payload = json.dumps({"partner_id": "wap", "pageSize": 20})
        response = self.session.post(
            self.HOT_API,
            data=payload,
            headers=headers,
            timeout=15,
        )
        data = response.json()
        items = data.get("data", {}).get("hotRankList", [])
        if not items:
            items = data.get("data", {}).get("items", [])
        results = []
        for item in items[:20]:
            title = item.get("title", "").strip()
            if not title:
                continue
            article_id = item.get("entityId", item.get("id", ""))
            source_id = hashlib.md5(f"36kr_{article_id}".encode()).hexdigest()[:16]
            summary = item.get("summary", item.get("description", title))[:500]
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
        return results

    def _crawl_web_page(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://36kr.com/"
        for url in [self.HOT_URL, self.AI_URL]:
            try:
                response = self.fetch(url, headers=headers)
                html = response.text
                results = self._parse_article_list(html)
                if results:
                    return results
            except Exception:
                continue
        return []

    def _parse_article_list(self, html: str) -> list:
        results = []
        try:
            match = re.search(r'window\.initialState\s*=\s*({.*?});\s*</script>', html, re.DOTALL)
            if match:
                json_str = match.group(1)
                state = json.loads(json_str)
                articles = state.get("hotListModule", {}).get("hotList", [])
                if not articles:
                    articles = state.get("catalogListModule", {}).get("catalogList", [])
                if not articles:
                    articles = state.get("articleListModule", {}).get("articleList", [])
                for article in articles[:20]:
                    title = article.get("title", "").strip()
                    if not title:
                        continue
                    article_id = article.get("entityId", article.get("id", ""))
                    source_id = hashlib.md5(f"36kr_{article_id}".encode()).hexdigest()[:16]
                    summary = article.get("summary", title)[:500]
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
            self.logger.warning(f"36氪页面解析失败: {e}")

        if not results:
            article_pattern = re.findall(r'href="/p/(\d+)"[^>]*>([^<]{6,}?)</a>', html, re.DOTALL)
            seen = set()
            for article_id, title in article_pattern[:20]:
                title = title.strip()
                if not title or article_id in seen:
                    continue
                seen.add(article_id)
                source_id = hashlib.md5(f"36kr_{article_id}".encode()).hexdigest()[:16]
                results.append({
                    "source_id": source_id,
                    "title": title[:40],
                    "content": title[:500],
                    "source_url": f"https://36kr.com/p/{article_id}",
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
            headers["Referer"] = "https://36kr.com/"
            headers["Content-Type"] = "application/json"

            try:
                article_id = source_url.split("/p/")[-1].rstrip("/")
                payload = json.dumps({"articleId": article_id})
                response = self.session.post(
                    self.DETAIL_API,
                    data=payload,
                    headers=headers,
                    timeout=15,
                )
                data = response.json()
                article_data = data.get("data", {}).get("articleDetail", {})
                if not article_data:
                    article_data = data.get("data", {})
                content = article_data.get("content", "")
                if content:
                    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    content = re.sub(r'<[^>]+>', '', content)
                    content = re.sub(r'\s+', ' ', content).strip()
                    if len(content) >= 50:
                        return content[:500]
                summary = article_data.get("summary", "")
                if summary and len(summary) >= 50:
                    return summary[:500]
            except Exception:
                pass

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                match = re.search(r'class="article-content"[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
                if not match:
                    match = re.search(r'class="content"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1)
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
            self.logger.warning(f"36氪详情爬取失败: {e}")
            return ""
