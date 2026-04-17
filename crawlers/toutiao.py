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
    DETAIL_API = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
    ARTICLE_API = "https://www.toutiao.com/article/{article_id}/"

    def __init__(self):
        super().__init__("toutiao", "今日头条")

    def crawl(self) -> list:
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
                hot_desc = item.get("HotDesc", "")
                label = item.get("Label", "")
                content_parts = [title]
                if hot_desc and hot_desc != title:
                    content_parts.append(hot_desc)
                if label and label != title:
                    content_parts.append(label)
                content = "。".join(content_parts)
                results.append({
                    "source_id": source_id,
                    "title": title[:40],
                    "content": content[:500],
                    "source_url": f"https://www.toutiao.com/trending/{cluster_id}/",
                    "event_time": datetime.now(),
                    "core_entity": title[:20],
                    "location": "",
                    "indicator_name": "",
                    "indicator_value": "",
                    "_cluster_id": cluster_id,
                    "_hot_desc": hot_desc,
                    "_label": label,
                })
        except Exception as e:
            self.logger.error(f"头条爬取异常: {e}")
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.toutiao.com/"
            headers["Accept"] = "application/json, text/plain, */*"

            cluster_id = item.get("_cluster_id", "")
            if not cluster_id:
                cluster_id_match = re.search(r'/trending/(\d+)', source_url)
                if cluster_id_match:
                    cluster_id = cluster_id_match.group(1)

            if cluster_id:
                try:
                    detail_api = f"{self.DETAIL_API}&cluster_id={cluster_id}"
                    detail_data = self.fetch_json(detail_api, headers=headers)
                    articles = detail_data.get("data", [])
                    target_item = None
                    for art in articles:
                        if str(art.get("ClusterId", "")) == str(cluster_id):
                            target_item = art
                            break
                    if not target_item and articles:
                        target_item = articles[0]

                    if target_item:
                        title = target_item.get("Title", "")
                        hot_desc = target_item.get("HotDesc", "")
                        abstract = target_item.get("Abstract", "")
                        label = target_item.get("Label", "")
                        content_parts = []
                        if title:
                            content_parts.append(title)
                        if hot_desc and hot_desc != title:
                            content_parts.append(hot_desc)
                        if abstract and abstract != title and abstract != hot_desc:
                            content_parts.append(abstract)
                        if label and label != title and label != hot_desc:
                            content_parts.append(f"标签: {label}")
                        combined = "。".join(content_parts)
                        if len(combined) >= 50:
                            return combined[:500]
                except Exception:
                    pass

            try:
                search_url = f"https://www.toutiao.com/api/search/content/?keyword={item.get('title', '')}&count=5"
                search_data = self.fetch_json(search_url, headers=headers)
                search_items = search_data.get("data", [])
                if search_items:
                    for s_item in search_items[:3]:
                        s_content = s_item.get("abstract", s_item.get("content", ""))
                        if s_content:
                            s_content = re.sub(r'<[^>]+>', '', s_content)
                            s_content = re.sub(r'\s+', ' ', s_content).strip()
                            if len(s_content) >= 50:
                                return s_content[:500]
            except Exception:
                pass

            return ""
        except Exception as e:
            self.logger.warning(f"头条详情爬取失败: {e}")
            return ""
