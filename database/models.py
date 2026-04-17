"""
信息聚合系统 - 数据库模型定义
使用SQLAlchemy ORM定义渠道表、分类表、信息主表
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Category(Base):
    """
    分类表：存储信息分类（热点事件/经济数据/国际大事/科技动向/AI大模型动向）
    支持动态扩展分类，新增分类只需插入记录
    """
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(50), nullable=False, unique=True, comment="分类名称")
    code = Column(String(50), nullable=False, unique=True, comment="分类编码")
    description = Column(String(200), default="", comment="分类描述")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    infos = relationship("Info", back_populates="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', code='{self.code}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }


class Channel(Base):
    """
    渠道表：存储信息来源渠道（微博/头条/CSDN等）
    支持动态扩展渠道，新增渠道只需插入记录并实现对应爬虫
    """
    __tablename__ = "channel"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="渠道ID")
    name = Column(String(50), nullable=False, unique=True, comment="渠道名称")
    code = Column(String(50), nullable=False, unique=True, comment="渠道编码")
    base_url = Column(String(255), default="", comment="渠道基础URL")
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False, comment="关联分类ID")
    crawl_interval = Column(Integer, default=60, comment="爬取间隔(分钟)")
    is_active = Column(Integer, default=1, comment="是否启用 1-启用 0-禁用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    infos = relationship("Info", back_populates="channel", lazy="dynamic")
    category_rel = relationship("Category", lazy="joined")

    def __repr__(self):
        return f"<Channel(id={self.id}, name='{self.name}', code='{self.code}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "base_url": self.base_url,
            "category_id": self.category_id,
            "category_name": self.category_rel.name if self.category_rel else "",
            "crawl_interval": self.crawl_interval,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }


class Info(Base):
    """
    信息主表：存储爬取到的所有信息
    通过channel_id关联渠道，通过category_id关联分类
    使用source_id+channel_id做去重唯一约束
    """
    __tablename__ = "info"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="信息ID")
    title = Column(String(200), nullable=False, comment="标题(≤40字)")
    content = Column(Text, default="", comment="内容/事件详情(150-500字)")
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False, comment="分类ID")
    channel_id = Column(Integer, ForeignKey("channel.id"), nullable=False, comment="渠道ID")
    source_id = Column(String(100), default="", comment="来源唯一标识(用于去重)")
    source_url = Column(String(500), default="", comment="来源URL")
    event_time = Column(DateTime, comment="事件发生时间")
    core_entity = Column(String(100), default="", comment="核心主体/人物")
    location = Column(String(100), default="", comment="地点")
    indicator_name = Column(String(100), default="", comment="指标名称(经济数据类)")
    indicator_value = Column(String(100), default="", comment="指标数值(经济数据类)")
    detail_fetch_status = Column(String(20), default="pending", comment="详情爬取状态: pending/success/failed")
    detail_fetch_error = Column(String(500), default="", comment="详情爬取失败原因")
    is_deleted = Column(Integer, default=0, comment="逻辑删除 0-正常 1-删除")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    channel = relationship("Channel", back_populates="infos", lazy="joined")
    category = relationship("Category", back_populates="infos", lazy="joined")

    __table_args__ = (
        UniqueConstraint("source_id", "channel_id", name="uq_source_channel"),
        Index("idx_category_id", "category_id"),
        Index("idx_channel_id", "channel_id"),
        Index("idx_event_time", "event_time"),
        Index("idx_created_at", "created_at"),
        Index("idx_detail_fetch_status", "detail_fetch_status"),
    )

    def __repr__(self):
        return f"<Info(id={self.id}, title='{self.title[:20]}...')>"

    def to_dict(self):
        """将信息记录转换为字典，用于API返回"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "",
            "channel_id": self.channel_id,
            "channel_name": self.channel.name if self.channel else "",
            "source_id": self.source_id,
            "source_url": self.source_url,
            "event_time": self.event_time.strftime("%Y-%m-%d %H:%M:%S") if self.event_time else None,
            "core_entity": self.core_entity,
            "location": self.location,
            "indicator_name": self.indicator_name,
            "indicator_value": self.indicator_value,
            "detail_fetch_status": self.detail_fetch_status,
            "detail_fetch_error": self.detail_fetch_error,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
