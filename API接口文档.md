# 信息聚合系统 API接口文档

## 1. 系统概述

信息聚合系统（Info_aggregation）是一个多渠道信息爬取和聚合的系统，提供热点事件、经济数据、国际大事、科技动向、AI大模型动向等信息的查询接口。

### 1.1 基础信息

- **服务地址**：`http://localhost:8000`（默认）
- **API文档**：`http://localhost:8000/docs`（Swagger UI）
- **系统版本**：1.0.0
- **响应格式**：统一JSON格式，包含code、message、data字段

## 2. 接口列表

| 接口路径 | 方法 | 功能描述 | 权限 |
|---------|------|----------|------|
| `/` | GET | 系统根路径，返回系统信息 | 公开 |
| `/api/categories` | GET | 获取所有信息分类 | 公开 |
| `/api/channels` | GET | 获取渠道列表 | 公开 |
| `/api/infos` | GET | 分页查询信息列表 | 公开 |
| `/api/infos/{info_id}` | GET | 获取单条信息详情 | 公开 |
| `/api/stats` | GET | 获取系统统计信息 | 公开 |
| `/api/crawl/trigger` | POST | 手动触发爬取任务 | 公开 |

## 3. 详细接口说明

### 3.1 系统信息接口

**接口路径**：`/`

**请求方法**：GET

**功能描述**：返回系统基本信息，用于健康检查

**请求参数**：无

**成功响应**：
```json
{
  "system": "信息聚合系统",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2026-04-17 12:00:00"
}
```

### 3.2 获取分类列表

**接口路径**：`/api/categories`

**请求方法**：GET

**功能描述**：获取系统中所有的信息分类

**请求参数**：无

**成功响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "热点事件",
      "code": "hot",
      "description": "实时热点事件"
    },
    {
      "id": 2,
      "name": "经济数据",
      "code": "economy",
      "description": "经济指标数据"
    },
    {
      "id": 3,
      "name": "国际大事",
      "code": "international",
      "description": "国际新闻事件"
    },
    {
      "id": 4,
      "name": "科技动向",
      "code": "tech",
      "description": "科技领域动态"
    },
    {
      "id": 5,
      "name": "AI大模型动向",
      "code": "ai",
      "description": "人工智能大模型相关信息"
    }
  ]
}
```

### 3.3 获取渠道列表

**接口路径**：`/api/channels`

**请求方法**：GET

**功能描述**：获取系统中的信息来源渠道，支持按分类ID筛选

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| category_id | integer | 否 | 分类ID，用于筛选指定分类下的渠道 |

**成功响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "微博",
      "code": "weibo",
      "base_url": "https://weibo.com",
      "category_id": 1,
      "crawl_interval": 30,
      "is_active": 1
    },
    {
      "id": 2,
      "name": "今日头条",
      "code": "toutiao",
      "base_url": "https://www.toutiao.com",
      "category_id": 1,
      "crawl_interval": 30,
      "is_active": 1
    },
    {
      "id": 3,
      "name": "小红书",
      "code": "xiaohongshu",
      "base_url": "https://www.xiaohongshu.com",
      "category_id": 1,
      "crawl_interval": 30,
      "is_active": 1
    },
    {
      "id": 4,
      "name": "东方财富网",
      "code": "eastmoney",
      "base_url": "https://www.eastmoney.com",
      "category_id": 2,
      "crawl_interval": 60,
      "is_active": 1
    },
    {
      "id": 5,
      "name": "路透社",
      "code": "reuters",
      "base_url": "https://www.reuters.com",
      "category_id": 3,
      "crawl_interval": 120,
      "is_active": 1
    },
    {
      "id": 6,
      "name": "CSDN",
      "code": "csdn",
      "base_url": "https://www.csdn.net",
      "category_id": 4,
      "crawl_interval": 120,
      "is_active": 1
    },
    {
      "id": 7,
      "name": "掘金",
      "code": "juejin",
      "base_url": "https://juejin.cn",
      "category_id": 4,
      "crawl_interval": 120,
      "is_active": 1
    },
    {
      "id": 8,
      "name": "博客园",
      "code": "cnblogs",
      "base_url": "https://www.cnblogs.com",
      "category_id": 4,
      "crawl_interval": 120,
      "is_active": 1
    },
    {
      "id": 9,
      "name": "36氪",
      "code": "36kr",
      "base_url": "https://36kr.com",
      "category_id": 5,
      "crawl_interval": 120,
      "is_active": 1
    },
    {
      "id": 10,
      "name": "知乎",
      "code": "zhihu",
      "base_url": "https://www.zhihu.com",
      "category_id": 5,
      "crawl_interval": 120,
      "is_active": 1
    }
  ]
}
```

### 3.4 分页查询信息列表

**接口路径**：`/api/infos`

**请求方法**：GET

**功能描述**：分页查询信息列表，支持按分类、渠道、关键词筛选

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| category_id | integer | 否 | 分类ID，用于筛选指定分类的信息 |
| channel_id | integer | 否 | 渠道ID，用于筛选指定渠道的信息 |
| keyword | string | 否 | 关键词，用于搜索标题和内容 |
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20，最大100 |

**成功响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "title": "全国两会胜利闭幕",
        "content": "全国两会圆满闭幕，会议通过多项重要决议，涉及经济发展、民生改善等多个领域，为全年工作指明方向。今年两会重点讨论了GDP增长目标设定、财政赤字率安排、新质生产力培育等核心议题。代表委员们围绕扩大内需、促进就业、深化改革开放等提出大量建议，多项民生利好政策陆续出台，包括提高城乡居民收入、完善社会保障体系、推进教育公平等举措，为经济社会高质量发展注入强劲动力。",
        "category_id": 1,
        "category_name": "热点事件",
        "channel_id": 1,
        "channel_name": "微博",
        "source_id": "mock_wb_001",
        "source_url": "https://example.com/mock_wb_001",
        "event_time": "2026-04-17 10:00:00",
        "core_entity": "全国两会",
        "location": "北京",
        "indicator_name": "",
        "indicator_value": "",
        "detail_fetch_status": "success",
        "detail_fetch_error": "",
        "created_at": "2026-04-17 10:00:00",
        "updated_at": "2026-04-17 10:00:00"
      },
      {
        "id": 2,
        "title": "春季招聘市场持续升温",
        "content": "多地举办春季大型招聘会，人工智能、新能源等领域岗位需求旺盛，应届生就业形势总体向好。据人社部数据，今年春季招聘季全国累计举办线上线下招聘活动超过5万场，提供岗位信息超千万条。其中人工智能相关岗位同比增长超过80%，新能源、半导体、生物医药等战略性新兴产业招聘需求持续攀升。各地政府出台就业补贴、人才公寓等政策吸引青年人才，高校毕业生签约率较去年同期提升约5个百分点。",
        "category_id": 1,
        "category_name": "热点事件",
        "channel_id": 1,
        "channel_name": "微博",
        "source_id": "mock_wb_002",
        "source_url": "https://example.com/mock_wb_002",
        "event_time": "2026-04-17 09:30:00",
        "core_entity": "春季招聘",
        "location": "全国",
        "indicator_name": "",
        "indicator_value": "",
        "detail_fetch_status": "success",
        "detail_fetch_error": "",
        "created_at": "2026-04-17 09:30:00",
        "updated_at": "2026-04-17 09:30:00"
      }
    ]
  }
}
```

### 3.5 获取单条信息详情

**接口路径**：`/api/infos/{info_id}`

**请求方法**：GET

**功能描述**：根据信息ID获取单条信息的详细信息

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| info_id | integer | 是 | 信息ID |

**成功响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "title": "全国两会胜利闭幕",
    "content": "全国两会圆满闭幕，会议通过多项重要决议，涉及经济发展、民生改善等多个领域，为全年工作指明方向。今年两会重点讨论了GDP增长目标设定、财政赤字率安排、新质生产力培育等核心议题。代表委员们围绕扩大内需、促进就业、深化改革开放等提出大量建议，多项民生利好政策陆续出台，包括提高城乡居民收入、完善社会保障体系、推进教育公平等举措，为经济社会高质量发展注入强劲动力。",
    "category_id": 1,
    "category_name": "热点事件",
    "channel_id": 1,
    "channel_name": "微博",
    "source_id": "mock_wb_001",
    "source_url": "https://example.com/mock_wb_001",
    "event_time": "2026-04-17 10:00:00",
    "core_entity": "全国两会",
    "location": "北京",
    "indicator_name": "",
    "indicator_value": "",
    "detail_fetch_status": "success",
    "detail_fetch_error": "",
    "created_at": "2026-04-17 10:00:00",
    "updated_at": "2026-04-17 10:00:00"
  }
}
```

**错误响应**：
```json
{
  "detail": "信息不存在"
}
```

### 3.6 获取系统统计信息

**接口路径**：`/api/stats`

**请求方法**：GET

**功能描述**：获取系统中各分类的信息数量统计

**请求参数**：无

**成功响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 100,
    "categories": [
      {
        "name": "热点事件",
        "count": 30
      },
      {
        "name": "经济数据",
        "count": 15
      },
      {
        "name": "国际大事",
        "count": 20
      },
      {
        "name": "科技动向",
        "count": 20
      },
      {
        "name": "AI大模型动向",
        "count": 15
      }
    ]
  }
}
```

### 3.7 手动触发爬取任务

**接口路径**：`/api/crawl/trigger`

**请求方法**：POST

**功能描述**：手动触发指定渠道的爬取任务，立即执行爬取并返回结果

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| channel_code | string | 是 | 渠道编码，如：weibo、toutiao、xiaohongshu等 |

**成功响应**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "channel": "weibo",
    "raw_count": 20,
    "cleaned_count": 15,
    "detail_fetched": 15
  }
}
```

**错误响应**：
```json
{
  "detail": "渠道 xxx 未注册"
}
```

## 4. 数据结构说明

### 4.1 信息对象（Info）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 信息ID |
| title | string | 标题（≤40字） |
| content | string | 内容/事件详情（150-500字） |
| category_id | integer | 分类ID |
| category_name | string | 分类名称 |
| channel_id | integer | 渠道ID |
| channel_name | string | 渠道名称 |
| source_id | string | 来源唯一标识（用于去重） |
| source_url | string | 来源URL |
| event_time | string | 事件发生时间（YYYY-MM-DD HH:MM:SS） |
| core_entity | string | 核心主体/人物 |
| location | string | 地点 |
| indicator_name | string | 指标名称（经济数据类） |
| indicator_value | string | 指标数值（经济数据类） |
| detail_fetch_status | string | 详情爬取状态：pending/success/failed |
| detail_fetch_error | string | 详情爬取失败原因 |
| created_at | string | 创建时间（YYYY-MM-DD HH:MM:SS） |
| updated_at | string | 更新时间（YYYY-MM-DD HH:MM:SS） |

### 4.2 分类对象（Category）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 分类ID |
| name | string | 分类名称 |
| code | string | 分类编码 |
| description | string | 分类描述 |

### 4.3 渠道对象（Channel）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 渠道ID |
| name | string | 渠道名称 |
| code | string | 渠道编码 |
| base_url | string | 渠道基础URL |
| category_id | integer | 关联分类ID |
| crawl_interval | integer | 爬取间隔（分钟） |
| is_active | integer | 是否启用（1-启用，0-禁用） |

## 5. 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 请求参数验证失败 |
| 500 | 服务器内部错误 |

## 6. 调用示例

### 6.1 获取分类列表

```bash
curl http://localhost:8000/api/categories
```

### 6.2 分页查询信息（带筛选）

```bash
curl "http://localhost:8000/api/infos?category_id=1&keyword=两会&page=1&page_size=10"
```

### 6.3 获取信息详情

```bash
curl http://localhost:8000/api/infos/1
```

### 6.4 触发爬取任务

```bash
curl -X POST "http://localhost:8000/api/crawl/trigger?channel_code=weibo"
```

## 7. 注意事项

1. **接口限流**：系统默认对API接口没有限流，但建议合理控制请求频率，避免过度请求导致服务不稳定

2. **数据更新**：系统会定期自动爬取数据，手动触发爬取可能会覆盖现有数据

3. **内容长度**：`content` 字段内容长度控制在150-500字之间，详情爬取失败时会保留原始摘要

4. **错误处理**：接口返回统一的错误格式，客户端需要根据 `code` 和 `message` 字段判断请求状态

5. **性能优化**：对于大批量数据查询，建议使用分页参数控制返回数据量，避免一次请求过多数据

## 8. 维护与支持

- **系统日志**：日志文件位于 `logs/info_aggregation.log`
- **服务重启**：修改配置或代码后，需要重启服务使变更生效
- **数据清理**：系统采用逻辑删除，定期清理过期数据可提高查询性能

---

**文档版本**：1.0.0
**生成时间**：2026-04-17
**适用系统**：信息聚合系统 v1.0.0