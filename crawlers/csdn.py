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
    通过CSDN网页端获取热门技术文章
    爬取频率：每2小时一次
    """

    HOT_API = "https://blog.csdn.net/api-user/feed/hot_article"
    HOME_URL = "https://www.csdn.net/nav/ai"

    def __init__(self):
        super().__init__("csdn", "CSDN")

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
            self.logger.error(f"CSDN爬取异常: {e}")
        return results

    def _crawl_api(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://blog.csdn.net/"
        data = self.fetch_json(self.HOT_API, headers=headers)
        articles = data.get("data", [])
        results = []
        for article in articles[:20]:
            title = article.get("title", "").strip()
            if not title:
                continue
            article_id = article.get("article_id", "")
            source_id = hashlib.md5(f"csdn_{article_id}".encode()).hexdigest()[:16]
            desc = article.get("desc", title)[:500]
            url = article.get("url", f"https://blog.csdn.net/article/details/{article_id}")
            results.append({
                "source_id": source_id,
                "title": title[:40],
                "content": desc,
                "source_url": url,
                "event_time": datetime.now(),
                "core_entity": title[:20],
                "location": "",
                "indicator_name": "",
                "indicator_value": "",
            })
        return results

    def _crawl_web_page(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://www.csdn.net/"
        response = self.fetch(self.HOME_URL, headers=headers)
        html = response.text
        results = []
        article_pattern = re.findall(
            r'<a[^>]*href="(https://blog\.csdn\.net/[^/]+/article/details/(\d+))"[^>]*>\s*<span[^>]*>([^<]+)</span>',
            html, re.DOTALL
        )
        if not article_pattern:
            article_pattern = re.findall(
                r'<a[^>]*href="(https://blog\.csdn\.net/[^"]+article/details/(\d+))"[^>]*title="([^"]*)"',
                html, re.DOTALL
            )
        seen = set()
        for url, article_id, title in article_pattern:
            title = title.strip()
            if not title or article_id in seen:
                continue
            seen.add(article_id)
            source_id = hashlib.md5(f"csdn_{article_id}".encode()).hexdigest()[:16]
            results.append({
                "source_id": source_id,
                "title": title[:40],
                "content": title[:500],
                "source_url": url,
                "event_time": datetime.now(),
                "core_entity": title[:20],
                "location": "",
                "indicator_name": "",
                "indicator_value": "",
            })
            if len(results) >= 20:
                break
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://blog.csdn.net/"

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                match = re.search(r'id="article_content"[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
                if not match:
                    match = re.search(r'class="article_content"[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1)
                    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
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
            self.logger.warning(f"CSDN详情爬取失败: {e}")
            return ""
