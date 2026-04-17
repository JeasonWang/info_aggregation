"""
信息聚合系统 - 小红书爬虫
爬取小红书热门笔记，并深入爬取详情页获取完整内容
"""
import hashlib
import re
from datetime import datetime

from .base import BaseCrawler


class XiaohongshuCrawler(BaseCrawler):
    """
    小红书爬虫
    通过小红书探索页API获取热门笔记
    爬取频率：每30分钟一次
    """

    EXPLORE_API = "https://edith.xiaohongshu.com/api/sns/web/v1/homefeed"
    NOTE_DETAIL_API = "https://edith.xiaohongshu.com/api/sns/web/v1/feed"

    def __init__(self):
        super().__init__("xiaohongshu", "小红书")

    def crawl(self) -> list:
        """
        爬取小红书热门内容
        返回: 标准化信息列表
        """
        results = []
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.xiaohongshu.com/explore"
            data = self.fetch_json(self.EXPLORE_API, headers=headers)
            items = data.get("data", {}).get("items", [])
            for item in items[:20]:
                note_card = item.get("note_card", {})
                title = note_card.get("display_title", "").strip()
                if not title:
                    continue
                note_id = note_card.get("note_id", "")
                source_id = hashlib.md5(f"xhs_{note_id}".encode()).hexdigest()[:16]
                desc = note_card.get("desc", title)[:500]
                results.append({
                    "source_id": source_id,
                    "title": title[:40],
                    "content": desc,
                    "source_url": f"https://www.xiaohongshu.com/explore/{note_id}",
                    "event_time": datetime.now(),
                    "core_entity": title[:20],
                    "location": "",
                    "indicator_name": "",
                    "indicator_value": "",
                })
        except Exception as e:
            self.logger.error(f"小红书爬取异常: {e}")
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """
        爬取小红书笔记详情页，获取完整内容
        参数:
            source_url: 笔记详情页URL
            item: 基础信息字典
        返回: 完整内容文本
        """
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.xiaohongshu.com/"
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
                if match:
                    import json
                    json_str = match.group(1)
                    json_str = re.sub(r':undefined', ':null', json_str)
                    state = json.loads(json_str)
                    note_data = state.get("note", {}).get("noteDetailMap", {})
                    for note_id, note_info in note_data.items():
                        note = note_info.get("note", {})
                        desc = note.get("desc", "")
                        if desc and len(desc) >= 100:
                            return desc[:500]
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
            self.logger.warning(f"小红书详情爬取失败: {e}")
            return ""
