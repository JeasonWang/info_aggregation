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
    通过微博移动端页面获取实时热点事件
    爬取频率：每30分钟一次
    """

    HOT_SEARCH_API = "https://weibo.com/ajax/side/hotSearch"
    MOBILE_HOT_API = "https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot"
    HOT_BAND_API = "https://weibo.com/ajax/statuses/hot_band"

    def __init__(self):
        super().__init__("weibo", "微博")

    def crawl(self) -> list:
        results = []
        try:
            results = self._crawl_mobile_api()
            if results:
                return results
        except Exception:
            pass

        try:
            results = self._crawl_hot_band()
            if results:
                return results
        except Exception:
            pass

        try:
            results = self._crawl_web_page()
            if results:
                return results
        except Exception as e:
            self.logger.error(f"微博爬取异常: {e}")
        return results

    def _crawl_mobile_api(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://m.weibo.cn/"
        headers["Accept"] = "application/json, text/plain, */*"
        data = self.fetch_json(self.MOBILE_HOT_API, headers=headers)
        cards = data.get("data", {}).get("cards", [])
        results = []
        for card in cards:
            card_group = card.get("card_group", [])
            for item in card_group:
                desc = item.get("desc", "")
                title = desc.strip() if desc else ""
                if not title:
                    continue
                source_id = hashlib.md5(f"weibo_{title}".encode()).hexdigest()[:16]
                results.append({
                    "source_id": source_id,
                    "title": title[:40],
                    "content": title[:500],
                    "source_url": f"https://s.weibo.com/weibo?q=%23{title}%23",
                    "event_time": datetime.now(),
                    "core_entity": title[:20],
                    "location": "",
                    "indicator_name": "",
                    "indicator_value": "",
                })
            if len(results) >= 20:
                break
        return results[:20]

    def _crawl_hot_band(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://weibo.com/"
        headers["Accept"] = "application/json, text/plain, */*"
        headers["X-Requested-With"] = "XMLHttpRequest"
        data = self.fetch_json(self.HOT_BAND_API, headers=headers)
        band_list = data.get("data", {}).get("band_list", [])
        results = []
        for band in band_list[:20]:
            word = band.get("word", "").strip()
            if not word:
                continue
            note = band.get("note", word)
            raw_text = band.get("raw_text", "")
            desc = band.get("desc", "")
            content_parts = [note]
            if raw_text and raw_text != note:
                content_parts.append(raw_text)
            if desc and desc != note and desc != raw_text:
                content_parts.append(desc)
            content = "。".join(content_parts)
            source_id = hashlib.md5(f"weibo_{word}".encode()).hexdigest()[:16]
            results.append({
                "source_id": source_id,
                "title": word[:40],
                "content": content[:500],
                "source_url": f"https://s.weibo.com/weibo?q=%23{word}%23",
                "event_time": datetime.now(),
                "core_entity": word[:20],
                "location": "",
                "indicator_name": "",
                "indicator_value": "",
            })
        return results

    def _crawl_web_page(self) -> list:
        headers = self._build_headers()
        headers["Referer"] = "https://s.weibo.com/"
        url = "https://s.weibo.com/top/summary"
        response = self.fetch(url, headers=headers)
        html = response.text
        results = []
        pattern = r'<td class="td-02">\s*<a[^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
        for word in matches[:20]:
            word = word.strip()
            if not word:
                continue
            source_id = hashlib.md5(f"weibo_{word}".encode()).hexdigest()[:16]
            results.append({
                "source_id": source_id,
                "title": word[:40],
                "content": word[:500],
                "source_url": f"https://s.weibo.com/weibo?q=%23{word}%23",
                "event_time": datetime.now(),
                "core_entity": word[:20],
                "location": "",
                "indicator_name": "",
                "indicator_value": "",
            })
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://weibo.com/"
            headers["Accept"] = "application/json, text/plain, */*"
            headers["X-Requested-With"] = "XMLHttpRequest"

            word = item.get("title", "")

            try:
                search_detail = f"https://weibo.com/ajax/search/topic?query={word}&page=1"
                data = self.fetch_json(search_detail, headers=headers)
                statuses = data.get("data", {}).get("statuses", [])
                if statuses:
                    text_parts = []
                    for status in statuses[:3]:
                        text_data = status.get("text", "")
                        text_data = re.sub(r'<[^>]+>', '', text_data)
                        text_data = re.sub(r'\s+', ' ', text_data).strip()
                        if text_data:
                            text_parts.append(text_data)
                    combined = " ".join(text_parts)
                    if len(combined) >= 50:
                        return combined[:500]
            except Exception:
                pass

            try:
                mobile_url = f"https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{word}"
                data = self.fetch_json(mobile_url, headers=headers)
                cards = data.get("data", {}).get("cards", [])
                text_parts = []
                for card in cards[:3]:
                    mblog = card.get("mblog", {})
                    if mblog:
                        text = mblog.get("text", "")
                        text = re.sub(r'<[^>]+>', '', text)
                        text = re.sub(r'\s+', ' ', text).strip()
                        if text:
                            text_parts.append(text)
                combined = " ".join(text_parts)
                if len(combined) >= 50:
                    return combined[:500]
            except Exception:
                pass

            return ""
        except Exception as e:
            self.logger.warning(f"微博详情爬取失败: {e}")
            return ""
