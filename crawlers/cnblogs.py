"""
信息聚合系统 - 博客园爬虫
爬取博客园热门文章，并深入爬取详情页获取完整内容
"""
import hashlib
import re
from datetime import datetime

from .base import BaseCrawler


class CnblogsCrawler(BaseCrawler):
    """
    博客园爬虫
    通过博客园API获取热门文章
    爬取频率：每2小时一次
    """

    HOME_API = "https://home.cnblogs.com/api/articles/hot?p=1&limit=20"
    POST_API = "https://www.cnblogs.com/{blog_name}/p/{post_id}.html"

    def __init__(self):
        super().__init__("cnblogs", "博客园")

    def crawl(self) -> list:
        """
        爬取博客园热门文章
        返回: 标准化信息列表
        """
        results = []
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.cnblogs.com/"
            data = self.fetch_json(self.HOME_API, headers=headers)
            articles = data if isinstance(data, list) else data.get("articles", [])
            for article in articles[:20]:
                title = article.get("title", "").strip()
                if not title:
                    continue
                article_id = article.get("id", "")
                source_id = hashlib.md5(f"cnblogs_{article_id}".encode()).hexdigest()[:16]
                desc = article.get("summary", title)[:500]
                url = article.get("url", f"https://www.cnblogs.com/p/{article_id}")
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
        except Exception as e:
            self.logger.error(f"博客园爬取异常: {e}")
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """
        爬取博客园文章详情页，获取完整内容
        参数:
            source_url: 文章URL
            item: 基础信息字典
        返回: 完整内容文本
        """
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.cnblogs.com/"

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                match = re.search(r'id="cnblogs_post_body"[^>]*>(.*?)</div>\s*<!--end: blogpost-body', html, re.DOTALL | re.IGNORECASE)
                if not match:
                    match = re.search(r'class="post-body"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
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
            self.logger.warning(f"博客园详情爬取失败: {e}")
            return ""
