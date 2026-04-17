"""
信息聚合系统 - FastAPI接口模块
提供信息查询、分类查询、渠道查询等RESTful API
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import get_session, Category, Channel, Info

logger = logging.getLogger(__name__)


class CategoryPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(default="", max_length=200)


class ChannelPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    base_url: str = Field(default="", max_length=255)
    category_id: int
    crawl_interval: int = Field(default=60, ge=1)
    is_active: int = Field(default=1, ge=0, le=1)

app = FastAPI(
    title="信息聚合系统 API",
    description="多渠道信息聚合系统，提供热点事件、经济数据、国际大事、科技动向、AI大模型动向等信息查询",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """系统根路径，返回系统信息"""
    return {
        "system": "信息聚合系统",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/api/categories")
def list_categories():
    """
    获取所有信息分类
    返回: 分类列表
    """
    session = get_session()
    try:
        categories = session.query(Category).all()
        return {
            "code": 0,
            "message": "success",
            "data": [c.to_dict() for c in categories],
        }
    finally:
        session.close()


@app.get("/api/channels")
def list_channels(
    category_id: Optional[int] = Query(None, description="按分类ID筛选"),
    include_inactive: bool = Query(False, description="是否包含停用渠道"),
):
    """
    获取渠道列表
    参数:
        category_id: 可选，按分类ID筛选
    返回: 渠道列表
    """
    session = get_session()
    try:
        query = session.query(Channel)
        if category_id:
            query = query.filter(Channel.category_id == category_id)
        if not include_inactive:
            query = query.filter(Channel.is_active == 1)
        channels = query.order_by(Channel.id.asc()).all()
        return {
            "code": 0,
            "message": "success",
            "data": [ch.to_dict() for ch in channels],
        }
    finally:
        session.close()


@app.get("/api/admin/categories")
def admin_list_categories():
    session = get_session()
    try:
        categories = session.query(Category).order_by(Category.id.asc()).all()
        return {
            "code": 0,
            "message": "success",
            "data": [item.to_dict() for item in categories],
        }
    finally:
        session.close()


@app.post("/api/admin/categories")
def admin_create_category(payload: CategoryPayload):
    session = get_session()
    try:
        if session.query(Category).filter(Category.name == payload.name).first():
            raise HTTPException(status_code=400, detail="分类名称已存在")
        if session.query(Category).filter(Category.code == payload.code).first():
            raise HTTPException(status_code=400, detail="分类编码已存在")

        category = Category(
            name=payload.name.strip(),
            code=payload.code.strip(),
            description=payload.description.strip(),
        )
        session.add(category)
        session.commit()
        session.refresh(category)
        return {
            "code": 0,
            "message": "success",
            "data": category.to_dict(),
        }
    finally:
        session.close()


@app.put("/api/admin/categories/{category_id}")
def admin_update_category(category_id: int, payload: CategoryPayload):
    session = get_session()
    try:
        category = session.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        if session.query(Category).filter(Category.name == payload.name, Category.id != category_id).first():
            raise HTTPException(status_code=400, detail="分类名称已存在")
        if session.query(Category).filter(Category.code == payload.code, Category.id != category_id).first():
            raise HTTPException(status_code=400, detail="分类编码已存在")

        category.name = payload.name.strip()
        category.code = payload.code.strip()
        category.description = payload.description.strip()
        session.commit()
        session.refresh(category)
        return {
            "code": 0,
            "message": "success",
            "data": category.to_dict(),
        }
    finally:
        session.close()


@app.get("/api/admin/channels")
def admin_list_channels():
    session = get_session()
    try:
        channels = session.query(Channel).order_by(Channel.id.asc()).all()
        return {
            "code": 0,
            "message": "success",
            "data": [item.to_dict() for item in channels],
        }
    finally:
        session.close()


@app.post("/api/admin/channels")
def admin_create_channel(payload: ChannelPayload):
    session = get_session()
    try:
        if not session.query(Category).filter(Category.id == payload.category_id).first():
            raise HTTPException(status_code=400, detail="分类不存在")
        if session.query(Channel).filter(Channel.name == payload.name).first():
            raise HTTPException(status_code=400, detail="渠道名称已存在")
        if session.query(Channel).filter(Channel.code == payload.code).first():
            raise HTTPException(status_code=400, detail="渠道编码已存在")

        channel = Channel(
            name=payload.name.strip(),
            code=payload.code.strip(),
            base_url=payload.base_url.strip(),
            category_id=payload.category_id,
            crawl_interval=payload.crawl_interval,
            is_active=payload.is_active,
        )
        session.add(channel)
        session.commit()
        session.refresh(channel)
        return {
            "code": 0,
            "message": "success",
            "data": channel.to_dict(),
        }
    finally:
        session.close()


@app.put("/api/admin/channels/{channel_id}")
def admin_update_channel(channel_id: int, payload: ChannelPayload):
    session = get_session()
    try:
        channel = session.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="渠道不存在")
        if not session.query(Category).filter(Category.id == payload.category_id).first():
            raise HTTPException(status_code=400, detail="分类不存在")
        if session.query(Channel).filter(Channel.name == payload.name, Channel.id != channel_id).first():
            raise HTTPException(status_code=400, detail="渠道名称已存在")
        if session.query(Channel).filter(Channel.code == payload.code, Channel.id != channel_id).first():
            raise HTTPException(status_code=400, detail="渠道编码已存在")

        channel.name = payload.name.strip()
        channel.code = payload.code.strip()
        channel.base_url = payload.base_url.strip()
        channel.category_id = payload.category_id
        channel.crawl_interval = payload.crawl_interval
        channel.is_active = payload.is_active
        session.commit()
        session.refresh(channel)
        return {
            "code": 0,
            "message": "success",
            "data": channel.to_dict(),
        }
    finally:
        session.close()


@app.get("/api/infos")
def list_infos(
    category_id: Optional[int] = Query(None, description="按分类ID筛选"),
    channel_id: Optional[int] = Query(None, description="按渠道ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    分页查询信息列表
    参数:
        category_id: 可选，按分类ID筛选
        channel_id: 可选，按渠道ID筛选
        keyword: 可选，关键词搜索（标题/内容）
        page: 页码，默认1
        page_size: 每页数量，默认20
    返回: 分页信息列表
    """
    session = get_session()
    try:
        query = session.query(Info).filter(Info.is_deleted == 0)

        if category_id:
            query = query.filter(Info.category_id == category_id)
        if channel_id:
            query = query.filter(Info.channel_id == channel_id)
        if keyword:
            query = query.filter(
                (Info.title.contains(keyword)) | (Info.content.contains(keyword))
            )

        total = query.count()
        items = query.order_by(Info.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "code": 0,
            "message": "success",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": [item.to_dict() for item in items],
            },
        }
    finally:
        session.close()


@app.get("/api/infos/{info_id}")
def get_info(info_id: int):
    """
    获取单条信息详情
    参数:
        info_id: 信息ID
    返回: 信息详情
    """
    session = get_session()
    try:
        info = session.query(Info).filter(Info.id == info_id, Info.is_deleted == 0).first()
        if not info:
            raise HTTPException(status_code=404, detail="信息不存在")
        return {
            "code": 0,
            "message": "success",
            "data": info.to_dict(),
        }
    finally:
        session.close()


@app.get("/api/stats")
def get_stats():
    """
    获取系统统计信息
    返回: 各分类信息数量统计
    """
    session = get_session()
    try:
        from sqlalchemy import func
        stats = (
            session.query(
                Category.name,
                func.count(Info.id).label("count"),
            )
            .outerjoin(Info, Info.category_id == Category.id)
            .filter(Info.is_deleted == 0)
            .group_by(Category.id)
            .all()
        )
        total = session.query(Info).filter(Info.is_deleted == 0).count()
        return {
            "code": 0,
            "message": "success",
            "data": {
                "total": total,
                "categories": [
                    {"name": name, "count": count}
                    for name, count in stats
                ],
            },
        }
    finally:
        session.close()


@app.post("/api/crawl/trigger")
def trigger_crawl(channel_code: str = Query(..., description="渠道编码")):
    """
    手动触发指定渠道的爬取任务
    参数:
        channel_code: 渠道编码
    返回: 爬取结果
    """
    from crawlers.registry import crawler_registry
    from cleaners import clean_info_list

    crawler = crawler_registry.get(channel_code)
    if not crawler:
        raise HTTPException(status_code=404, detail=f"渠道 {channel_code} 未注册")

    raw_items = crawler.safe_crawl()
    cleaned_items = clean_info_list(raw_items)

    from scheduler import _save_crawled_data, _fetch_details_for_items

    saved_ids = _save_crawled_data(channel_code, cleaned_items)
    _fetch_details_for_items(channel_code, saved_ids)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "channel": channel_code,
            "raw_count": len(raw_items),
            "cleaned_count": len(cleaned_items),
            "detail_fetched": len(saved_ids),
        },
    }
