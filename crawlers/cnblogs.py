"""
信息聚合系统 - 博客园爬虫
爬取博客园热门技术文章，并深入爬取详情页获取完整内容
"""
import hashlib
import re
from datetime import datetime

from .base import BaseCrawler


class CnblogsCrawler(BaseCrawler):
    """
    博客园爬虫
    通过博客园API和网页端获取热门技术文章
    爬取频率：每2小时一次
    """

    SITE_HOME_URL = "https://www.cnblogs.com/sitehome/p/1"
    AGG_SITE_URL = "https://www.cnblogs.com/aggsite/top"
    PICK_URL = "https://www.cnblogs.com/pick/"

    def __init__(self):
        super().__init__("cnblogs", "博客园")

    def crawl(self) -> list:
        results = []
        for url in [self.AGG_SITE_URL, self.PICK_URL, self.SITE_HOME_URL]:
            try:
                results = self._crawl_web_page(url)
                if results:
                    return results
            except Exception:
                continue
        return results

    def _crawl_web_page(self, url: str) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://www.cnblogs.com/"
        response = self.fetch(url, headers=headers)
        html = response.text
        results = []
        post_pattern = re.findall(
            r'<a[^>]*class="post-item-title"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
            html, re.DOTALL
        )
        if not post_pattern:
            post_pattern = re.findall(
                r'<a[^>]*href="(https://www\.cnblogs\.com/[^/]+/p/[^"]+)"[^>]*class="titlelnk"[^>]*>([^<]+)</a>',
                html, re.DOTALL
            )
        if not post_pattern:
            post_pattern = re.findall(
                r'<a[^>]*href="(https://www\.cnblogs\.com/[^/]+/p/[^"]+)"[^>]*>([^<]{6,}?)</a>',
                html, re.DOTALL
            )
        seen = set()
        for post_url, title in post_pattern[:20]:
            title = title.strip()
            if not title or post_url in seen:
                continue
            seen.add(post_url)
            post_id = hashlib.md5(post_url.encode()).hexdigest()[:16]
            source_id = hashlib.md5(f"cnblogs_{post_id}".encode()).hexdigest()[:16]
            results.append({
                "source_id": source_id,
                "title": title[:40],
                "content": title[:500],
                "source_url": post_url,
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
            headers["Referer"] = "https://www.cnblogs.com/"

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                match = re.search(r'id="cnblogs_post_body"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL | re.IGNORECASE)
                if not match:
                    match = re.search(r'class="cnblogs-post-body"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL | re.IGNORECASE)
                if not match:
                    match = re.search(r'id="article_content"[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1)
                    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
                    content = re.sub(r'<pre[^>]*>.*?</pre>', '', content, flags=re.DOTALL | re.IGNORECASE)
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
            self.logger.warning(f"博客园详情爬取失败: {e}")
            return ""
