"""
信息聚合系统 - 微博热搜爬虫
爬取微博热搜榜，获取热点事件信息，并深入爬取详情页获取完整内容
"""
import hashlib
import re
from datetime import datetime

from .base import BaseCrawler


class WeiboCrawler(BaseCrawler):
    """
    微博热搜爬虫
    通过微博热搜API获取实时热点事件
    爬取频率：每30分钟一次
    """

    HOT_SEARCH_API = "https://weibo.com/ajax/side/hotSearch"
    DETAIL_API = "https://weibo.com/ajax/statuses/show"

    def __init__(self):
        super().__init__("weibo", "微博")

    def crawl(self) -> list:
        """
        爬取微博热搜
        返回: 标准化信息列表
        """
        results = []
        try:
            data = self.fetch_json(self.HOT_SEARCH_API)
            realtime = data.get("data", {}).get("realtime", [])
            for item in realtime[:20]:
                word = item.get("word", "").strip()
                if not word:
                    continue
                note = item.get("note", word)
                source_id = hashlib.md5(f"weibo_{word}".encode()).hexdigest()[:16]
                results.append({
                    "source_id": source_id,
                    "title": word[:40],
                    "content": note[:500] if note else word[:500],
                    "source_url": f"https://s.weibo.com/weibo?q=%23{word}%23",
                    "event_time": datetime.now(),
                    "core_entity": word[:20],
                    "location": "",
                    "indicator_name": "",
                    "indicator_value": "",
                })
        except Exception as e:
            self.logger.error(f"微博爬取异常: {e}")
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """
        爬取微博话题详情页，获取完整事件描述
        参数:
            source_url: 话题搜索页URL
            item: 基础信息字典
        返回: 完整内容文本
        """
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://weibo.com/"
            headers["Accept"] = "application/json, text/plain, */*"
            headers["X-Requested-With"] = "XMLHttpRequest"

            word = item.get("title", "")
            search_api = f"https://weibo.com/ajax/side/hotSearch"
            detail_api = f"https://weibo.com/ajax/statuses/hot_band"
            try:
                data = self.fetch_json(detail_api, headers=headers)
                band_list = data.get("data", {}).get("band_list", [])
                for band in band_list:
                    word_key = band.get("word", "")
                    if word_key and word in word_key:
                        note = band.get("note", "")
                        raw_text = band.get("raw_text", "")
                        desc = band.get("desc", "")
                        parts = []
                        if note:
                            parts.append(note)
                        if raw_text and raw_text != note:
                            parts.append(raw_text)
                        if desc and desc != note and desc != raw_text:
                            parts.append(desc)
                        full_text = "。".join(parts)
                        if len(full_text) >= 100:
                            return full_text[:500]
            except Exception:
                pass

            try:
                search_detail = f"https://weibo.com/ajax/search/topic?query={word}&page=1"
                data = self.fetch_json(search_detail, headers=headers)
                statuses = data.get("data", {}).get("statuses", [])
                if statuses:
                    top_status = statuses[0]
                    text_data = top_status.get("text", "")
                    text_data = re.sub(r'<[^>]+>', '', text_data)
                    text_data = re.sub(r'\s+', ' ', text_data).strip()
                    if len(text_data) >= 100:
                        return text_data[:500]
                    long_text = top_status.get("isLongText", False)
                    if long_text:
                        mid = top_status.get("mid", top_status.get("id", ""))
                        if mid:
                            longtext_api = f"https://weibo.com/ajax/statuses/longtext?id={mid}"
                            lt_data = self.fetch_json(longtext_api, headers=headers)
                            lt_text = lt_data.get("data", {}).get("longTextContent", "")
                            lt_text = re.sub(r'<[^>]+>', '', lt_text)
                            lt_text = re.sub(r'\s+', ' ', lt_text).strip()
                            if len(lt_text) >= 100:
                                return lt_text[:500]
            except Exception:
                pass

            return ""
        except Exception as e:
            self.logger.warning(f"微博详情爬取失败: {e}")
            return ""
