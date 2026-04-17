"""
信息聚合系统 - 小红书爬虫
爬取小红书热门笔记，使用桌面版探索页+详情页获取完整内容
"""
import hashlib
import re
import json
from datetime import datetime

from .base import BaseCrawler


class XiaohongshuCrawler(BaseCrawler):
    """
    小红书爬虫
    通过小红书桌面端获取热门笔记
    爬取频率：每30分钟一次
    """

    EXPLORE_URL = "https://www.xiaohongshu.com/explore"
    DETAIL_URL_TEMPLATE = "https://www.xiaohongshu.com/explore/{}"

    def __init__(self):
        super().__init__("xiaohongshu", "小红书")

    def _build_headers(self) -> dict:
        """构建桌面版请求头"""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.xiaohongshu.com/",
            "Upgrade-Insecure-Requests": "1",
        }

    def _is_valid_content(self, text: str) -> bool:
        """检查内容是否有效，过滤掉错误页面和备案信息"""
        if not text or len(text.strip()) < 50:
            return False
        
        invalid_keywords = [
            "你访问的页面不见了",
            "沪ICP备",
            "营业执照",
            "增值电信业务经营许可证",
            "互联网药品信息服务资格证书",
            "行吟信息科技",
        ]
        
        for keyword in invalid_keywords:
            if keyword in text:
                return False
        
        return True

    def _extract_initial_state(self, html: str) -> dict:
        """从HTML中提取__INITIAL_STATE__ JSON数据"""
        match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>', html, re.DOTALL)
        if match:
            json_str = match.group(1)
            json_str = re.sub(r':undefined', ':null', json_str)
            try:
                return json.loads(json_str)
            except Exception as e:
                self.logger.warning(f"JSON解析失败: {e}")
        return {}

    def crawl(self) -> list:
        """执行爬取"""
        results = []
        try:
            headers = self._build_headers()
            response = self.fetch(self.EXPLORE_URL, headers=headers)
            html = response.text
            
            self.logger.info(f"探索页HTML长度: {len(html)}")
            
            state = self._extract_initial_state(html)
            if not state:
                self.logger.warning("未找到INITIAL_STATE数据")
                return results
            
            results = self._parse_feed_data(state)
            
        except Exception as e:
            self.logger.error(f"小红书爬取异常: {e}", exc_info=True)
        
        return results[:20]

    def _parse_feed_data(self, state: dict) -> list:
        """解析探索页feed数据"""
        results = []
        
        feeds = state.get('feed', {}).get('feeds', [])
        self.logger.info(f"解析到feed数量: {len(feeds)}")
        
        for feed_item in feeds:
            try:
                note_info = self._extract_note_from_feed(feed_item)
                if note_info:
                    results.append(note_info)
            except Exception as e:
                self.logger.warning(f"解析feed项失败: {e}")
        
        return results

    def _extract_note_from_feed(self, feed_item: dict) -> dict:
        """从feed项中提取笔记信息"""
        note_id = feed_item.get('id', '')
        xsec_token = feed_item.get('xsecToken', '')
        note_card = feed_item.get('noteCard', {})
        
        if not note_id:
            return None
        
        title = note_card.get('displayTitle', '').strip()
        if not title:
            return None
        
        source_id = hashlib.md5(f"xhs_{note_id}".encode()).hexdigest()[:16]
        
        source_url = f"{self.DETAIL_URL_TEMPLATE.format(note_id)}?xsec_token={xsec_token}" if xsec_token else self.DETAIL_URL_TEMPLATE.format(note_id)
        
        return {
            "source_id": source_id,
            "title": title[:40],
            "content": title[:500],
            "source_url": source_url,
            "event_time": datetime.now(),
            "core_entity": title[:20],
            "location": "",
            "indicator_name": "",
            "indicator_value": "",
            "_note_id": note_id,
            "_xsec_token": xsec_token,
        }

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """爬取详情页获取完整内容"""
        if not source_url:
            return ""
        
        try:
            headers = self._build_headers()
            response = self.fetch(source_url, headers=headers, timeout=15)
            html = response.text
            
            self.logger.info(f"详情页HTML长度: {len(html)}")
            
            if "你访问的页面不见了" in html:
                self.logger.warning("详情页返回'页面不见了'")
                return ""
            
            if "沪ICP备" in html and len(html) < 100000:
                self.logger.warning("详情页返回备案信息页面")
                return ""
            
            state = self._extract_initial_state(html)
            if state:
                content = self._extract_content_from_state(state)
                if content and self._is_valid_content(content):
                    return content[:500]
            
            text = self._extract_text_from_html(html)
            if text and self._is_valid_content(text):
                return text[:500]
            
            self.logger.warning("详情页未提取到有效内容")
            return ""
            
        except Exception as e:
            self.logger.warning(f"详情页爬取失败: {e}")
            return ""

    def _extract_content_from_state(self, state: dict) -> str:
        """从INITIAL_STATE中提取笔记内容"""
        note_data = state.get('note', {})
        detail_map = note_data.get('noteDetailMap', {})
        
        for note_id, note_info in detail_map.items():
            if note_id == 'undefined' or not isinstance(note_info, dict):
                continue
            
            note = note_info.get('note', {})
            if note:
                return self._combine_note_content(note)
        
        return ""

    def _combine_note_content(self, note: dict) -> str:
        """组合笔记标题和描述为完整内容"""
        title = note.get('title', '').strip()
        desc = note.get('desc', '').strip()
        
        content_parts = []
        if title:
            content_parts.append(title)
        if desc and desc != title:
            content_parts.append(desc)
        
        return "。".join(content_parts) if content_parts else ""
