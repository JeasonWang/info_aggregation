"""
信息聚合系统 - 知乎爬虫
爬取知乎AI/大模型相关热门话题，并深入爬取详情页获取完整内容
"""
import hashlib
import re
from datetime import datetime

from .base import BaseCrawler


class ZhihuCrawler(BaseCrawler):
    """
    知乎爬虫
    通过知乎API获取AI/大模型相关热门话题
    爬取频率：每2小时一次
    """

    HOT_API = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20"
    QUESTION_API = "https://www.zhihu.com/api/v4/questions/{question_id}/answers?limit=3&sort_by=default"

    def __init__(self):
        super().__init__("zhihu", "知乎")

    def crawl(self) -> list:
        """
        爬取知乎热榜
        返回: 标准化信息列表
        """
        results = []
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.zhihu.com/hot"
            headers["Cookie"] = ""
            data = self.fetch_json(self.HOT_API, headers=headers)
            items = data.get("data", [])
            for item in items[:20]:
                target = item.get("target", {})
                title = target.get("title", "").strip()
                if not title:
                    continue
                question_id = target.get("id", "")
                source_id = hashlib.md5(f"zhihu_{question_id}".encode()).hexdigest()[:16]
                excerpt = target.get("excerpt", title)[:500]
                results.append({
                    "source_id": source_id,
                    "title": title[:40],
                    "content": excerpt,
                    "source_url": f"https://www.zhihu.com/question/{question_id}",
                    "event_time": datetime.now(),
                    "core_entity": title[:20],
                    "location": "",
                    "indicator_name": "",
                    "indicator_value": "",
                })
        except Exception as e:
            self.logger.error(f"知乎爬取异常: {e}")
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        """
        爬取知乎问题详情页，获取高赞回答内容
        参数:
            source_url: 问题URL
            item: 基础信息字典
        返回: 完整内容文本
        """
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://www.zhihu.com/"
            headers["Accept"] = "application/json, text/plain, */*"

            try:
                question_id = source_url.split("/question/")[-1].split("/")[0].split("?")[0]
                answers_api = self.QUESTION_API.format(question_id=question_id)
                data = self.fetch_json(answers_api, headers=headers)
                answers = data.get("data", [])
                if answers:
                    for answer in answers:
                        content = answer.get("content", "")
                        if content:
                            content = re.sub(r'<[^>]+>', '', content)
                            content = re.sub(r'\s+', ' ', content).strip()
                            if len(content) >= 100:
                                return content[:500]
                    excerpt_parts = []
                    for answer in answers[:3]:
                        content = answer.get("excerpt", "")
                        if content:
                            excerpt_parts.append(content)
                    combined = " ".join(excerpt_parts)
                    if len(combined) >= 100:
                        return combined[:500]
            except Exception:
                pass

            try:
                response = self.fetch(source_url, headers=headers)
                html = response.text
                match = re.search(r'class="RichContent-inner"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1)
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
            self.logger.warning(f"知乎详情爬取失败: {e}")
            return ""
