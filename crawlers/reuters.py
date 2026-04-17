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
    通过路透社RSS和网页端获取国际新闻
    爬取频率：每2小时一次
    """

    NEWS_API = "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-section-alias-or-id-v1"
    RSS_URL = "https://www.reutersagency.com/feed/"
    WORLD_URL = "https://www.reuters.com/world/"

    def __init__(self):
        super().__init__("reuters", "路透社")

    def crawl(self) -> list:
        results = []
        try:
            results = self._crawl_api()
            if results:
                return results
        except Exception:
            pass

        try:
            results = self._crawl_rss()
            if results:
                return results
        except Exception:
            pass

        try:
            results = self._crawl_web_page()
            if results:
                return results
        except Exception as e:
            self.logger.error(f"路透社爬取异常: {e}")
        return results

    def _crawl_api(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://www.reuters.com/world/"
        params = {
            "size": 20,
            "section_alias": "world",
        }
        data = self.fetch_json(self.NEWS_API, params=params, headers=headers)
        articles = data.get("result", {}).get("articles", [])
        results = []
        for article in articles[:20]:
            title = article.get("title", "").strip()
            if not title:
                continue
            article_id = article.get("id", "")
            source_id = hashlib.md5(f"reuters_{article_id}".encode()).hexdigest()[:16]
            summary = article.get("description", title)[:500]
            article_url = article.get("canonical_url", article.get("url", ""))
            if article_url and not article_url.startswith("http"):
                article_url = f"https://www.reuters.com{article_url}"
            if not article_url:
                article_url = f"https://www.reuters.com/world/{article_id}/"
            results.append({
                "source_id": source_id,
                "title": title[:40],
                "content": summary,
                "source_url": article_url,
                "event_time": datetime.now(),
                "core_entity": title[:20],
                "location": "",
                "indicator_name": "",
                "indicator_value": "",
            })
        return results

    def _crawl_rss(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://www.reutersagency.com/"
        response = self.fetch(self.RSS_URL, headers=headers)
        xml_text = response.text
        results = []
        item_pattern = re.findall(r'<item>\s*<title><!\[CDATA\[(.*?)\]\]></title>.*?<link>(.*?)</link>.*?<description><!\[CDATA\[(.*?)\]\]></description>', xml_text, re.DOTALL)
        if not item_pattern:
            item_pattern = re.findall(r'<item>\s*<title>(.*?)</title>.*?<link>(.*?)</link>.*?<description>(.*?)</description>', xml_text, re.DOTALL)
        for title, link, desc in item_pattern[:20]:
            title = title.strip()
            if not title:
                continue
            source_id = hashlib.md5(f"reuters_{link}".encode()).hexdigest()[:16]
            desc = desc.strip() if desc else title
            results.append({
                "source_id": source_id,
                "title": title[:40],
                "content": desc[:500],
                "source_url": link.strip(),
                "event_time": datetime.now(),
                "core_entity": title[:20],
                "location": "",
                "indicator_name": "",
                "indicator_value": "",
            })
        return results

    def _crawl_web_page(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://www.reuters.com/"
        response = self.fetch(self.WORLD_URL, headers=headers)
        html = response.text
        results = []
        link_pattern = re.findall(r'href="(/world/[^"]+)"[^>]*>[\s\S]*?<span[^>]*>([^<]+)</span>', html, re.DOTALL)
        if not link_pattern:
            link_pattern = re.findall(r'href="(/world/[^"]+-\d{4}-\d{2}-\d{2}[^"]*)"[^>]*>([^<]{10,}?)</a>', html, re.DOTALL)
        seen = set()
        for path, title in link_pattern[:20]:
            title = title.strip()
            if not title or path in seen:
                continue
            seen.add(path)
            url = f"https://www.reuters.com{path}"
            source_id = hashlib.md5(f"reuters_{path}".encode()).hexdigest()[:16]
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
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.reuters.com/"

            try:
                import json
                payload = json.dumps({"url": source_url})
                post_headers = headers.copy()
                post_headers["Content-Type"] = "application/json"
                response = self.session.post(
                    self.ARTICLE_API if hasattr(self, 'ARTICLE_API') else "https://www.reuters.com/pf/api/v3/content/fetch/article-by-id-or-url-v1",
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
                    if len(full_text) >= 50:
                        return full_text[:500]
                rn_text = article.get("rn_text", "")
                if rn_text:
                    rn_text = re.sub(r'<[^>]+>', '', rn_text)
                    rn_text = re.sub(r'\s+', ' ', rn_text).strip()
                    if len(rn_text) >= 50:
                        return rn_text[:500]
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
            self.logger.warning(f"路透社详情爬取失败: {e}")
            return ""
