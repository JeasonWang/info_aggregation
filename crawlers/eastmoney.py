"""
信息聚合系统 - 东方财富网爬虫
爬取经济数据（金价、油价等），并深入爬取详情页获取完整分析内容
"""
import hashlib
import json
import re
from datetime import datetime

from .base import BaseCrawler


class EastmoneyCrawler(BaseCrawler):
    """
    东方财富网爬虫
    通过东方财富API获取实时经济指标数据
    爬取频率：每1小时一次
    """

    GOLD_API = "https://push2.eastmoney.com/api/qt/stock/get?secid=113.aum&fields=f43,f44,f45,f46,f47,f170"
    OIL_API = "https://push2.eastmoney.com/api/qt/stock/get?secid=113.sccl&fields=f43,f44,f45,f46,f47,f170"
    USD_API = "https://push2.eastmoney.com/api/qt/stock/get?secid=133.USDCNY&fields=f43,f44,f45,f46,f47,f170"
    NEWS_API = "https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery&param=%7B%22uid%22%3A%22%22%2C%22keyword%22%3A%22{keyword}%22%2C%22type%22%3A%5B%22cmsArticleWebOld%22%5D%2C%22client%22%3A%22web%22%2C%22clientType%22%3A%22web%22%2C%22clientVersion%22%3A%22curr%22%2C%22param%22%3A%7B%22cmsArticleWebOld%22%3A%7B%22searchScope%22%3A%22default%22%2C%22sort%22%3A%22default%22%2C%22pageIndex%22%3A1%2C%22pageSize%22%3A5%7D%7D%7D"

    def __init__(self):
        super().__init__("eastmoney", "东方财富网")

    def _fetch_indicator(self, url: str, name: str, unit: str) -> dict:
        try:
            headers = self._build_headers()
            headers["Referer"] = "https://quote.eastmoney.com/"
            data = self.fetch_json(url, headers=headers)
            d = data.get("data")
            if not d or not isinstance(d, dict):
                self.logger.warning(f"东方财富{name}API返回数据为空")
                return None
            current = d.get("f43", 0)
            change = d.get("f170", 0)
            if current:
                current_val = float(current) / 100 if abs(float(current)) > 10000 else float(current)
                change_val = float(change) / 100 if abs(float(change)) > 100 else float(change)
            else:
                current_val = 0
                change_val = 0
            source_id = hashlib.md5(f"eastmoney_{name}".encode()).hexdigest()[:16]
            direction = "涨" if change_val > 0 else "跌"
            content = (
                f"{name}当前报{current_val:.2f}{unit}，{direction}{abs(change_val):.2f}{unit}，"
                f"更新时间{datetime.now().strftime('%Y-%m-%d %H:%M')}。"
                f"数据来源：东方财富网实时行情。"
                f"{'市场情绪偏多，多头力量占优。' if change_val > 0 else '市场情绪偏空，空头力量占优。'}"
                f"投资者需关注后续走势变化及宏观经济政策影响。"
            )
            return {
                "source_id": source_id,
                "title": f"{name}: {current_val:.2f}{unit} {'↑' if change_val > 0 else '↓'}{abs(change_val):.2f}"[:40],
                "content": content[:500],
                "source_url": "https://quote.eastmoney.com/",
                "event_time": datetime.now(),
                "core_entity": name,
                "location": "",
                "indicator_name": name,
                "indicator_value": f"{current_val:.2f}{unit}",
            }
        except Exception as e:
            self.logger.error(f"东方财富{name}爬取异常: {e}")
            return None

    def crawl(self) -> list:
        results = []
        indicators = [
            (self.GOLD_API, "国际金价", "美元/盎司"),
            (self.OIL_API, "国际原油", "美元/桶"),
            (self.USD_API, "美元人民币汇率", ""),
        ]
        for url, name, unit in indicators:
            item = self._fetch_indicator(url, name, unit)
            if item:
                results.append(item)
        return results

    def fetch_detail(self, source_url: str, item: dict) -> str:
        try:
            indicator_name = item.get("indicator_name", "")
            if not indicator_name:
                return ""
            headers = self._build_headers()
            headers["Referer"] = "https://so.eastmoney.com/"
            headers["Accept"] = "application/json, text/plain, */*"

            try:
                search_url = f"https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery&param={json.dumps({'uid':'','keyword':indicator_name,'type':['cmsArticleWebOld'],'client':'web','clientType':'web','clientVersion':'curr','param':{'cmsArticleWebOld':{'searchScope':'default','sort':'default','pageIndex':1,'pageSize':3}}}, ensure_ascii=False)}"
                response = self.fetch(search_url, headers=headers)
                text = response.text
                json_match = re.search(r'jQuery\((.*)\)', text, re.DOTALL)
                if json_match:
                    search_data = json.loads(json_match.group(1))
                    articles = search_data.get("result", {}).get("cmsArticleWebOld", {}).get("list", [])
                    if articles:
                        article = articles[0]
                        article_url = article.get("url", "")
                        if article_url:
                            try:
                                art_response = self.fetch(article_url, headers=headers)
                                art_text = self._extract_text_from_html(art_response.text)
                                if len(art_text) >= 50:
                                    return art_text[:500]
                            except Exception:
                                pass
                        content = article.get("content", "")
                        if content:
                            content = re.sub(r'<[^>]+>', '', content)
                            content = re.sub(r'\s+', ' ', content).strip()
                            if len(content) >= 50:
                                return content[:500]
                        title = article.get("title", "")
                        summary = article.get("content", article.get("description", ""))
                        if summary:
                            summary = re.sub(r'<[^>]+>', '', summary)
                            summary = re.sub(r'\s+', ' ', summary).strip()
                        combined = f"{title}。{summary}" if title and summary else (title or summary or "")
                        if len(combined) >= 50:
                            return combined[:500]
            except Exception:
                pass

            return ""
        except Exception as e:
            self.logger.warning(f"东方财富详情爬取失败: {e}")
            return ""
