"""
信息聚合系统 - 数据库初始化与模拟数据
创建分类、渠道记录，并插入模拟数据以便程序启动时有数据返回
"""
import logging
from datetime import datetime, timedelta
import random

from database import get_session, init_db, Category, Channel, Info
from config import CATEGORIES, CHANNELS, CATEGORY_HOT, CATEGORY_ECONOMY, CATEGORY_INTERNATIONAL, CATEGORY_TECH, CATEGORY_AI

logger = logging.getLogger(__name__)


def init_categories(session) -> dict:
    """
    初始化分类数据
    参数:
        session: 数据库会话
    返回: {分类名称: 分类ID} 映射字典
    """
    category_map = {}
    category_defs = [
        {"name": CATEGORY_HOT, "code": "hot", "description": "微博、头条等平台的热点事件"},
        {"name": CATEGORY_ECONOMY, "code": "economy", "description": "金价、油价等经济数据指标"},
        {"name": CATEGORY_INTERNATIONAL, "code": "international", "description": "美国动向、中东战争等国际大事"},
        {"name": CATEGORY_TECH, "code": "tech", "description": "科技行业最新动向"},
        {"name": CATEGORY_AI, "code": "ai", "description": "AI与大模型领域最新进展"},
    ]
    for cat_def in category_defs:
        existing = session.query(Category).filter(Category.code == cat_def["code"]).first()
        if existing:
            category_map[cat_def["name"]] = existing.id
        else:
            cat = Category(
                name=cat_def["name"],
                code=cat_def["code"],
                description=cat_def["description"],
            )
            session.add(cat)
            session.flush()
            category_map[cat_def["name"]] = cat.id
            logger.info(f"创建分类: {cat_def['name']}")
    session.commit()
    return category_map


def init_channels(session, category_map: dict) -> dict:
    """
    初始化渠道数据
    参数:
        session: 数据库会话
        category_map: 分类名称到ID的映射
    返回: {渠道编码: 渠道ID} 映射字典
    """
    channel_map = {}
    channel_defs = [
        {"name": "微博", "code": "weibo", "base_url": "https://weibo.com", "category": CATEGORY_HOT, "interval": 30},
        {"name": "今日头条", "code": "toutiao", "base_url": "https://www.toutiao.com", "category": CATEGORY_HOT, "interval": 30},
        {"name": "小红书", "code": "xiaohongshu", "base_url": "https://www.xiaohongshu.com", "category": CATEGORY_HOT, "interval": 30},
        {"name": "东方财富网", "code": "eastmoney", "base_url": "https://www.eastmoney.com", "category": CATEGORY_ECONOMY, "interval": 60},
        {"name": "路透社", "code": "reuters", "base_url": "https://www.reuters.com", "category": CATEGORY_INTERNATIONAL, "interval": 120},
        {"name": "CSDN", "code": "csdn", "base_url": "https://blog.csdn.net", "category": CATEGORY_TECH, "interval": 120},
        {"name": "掘金", "code": "juejin", "base_url": "https://juejin.cn", "category": CATEGORY_TECH, "interval": 120},
        {"name": "博客园", "code": "cnblogs", "base_url": "https://www.cnblogs.com", "category": CATEGORY_TECH, "interval": 120},
        {"name": "36氪", "code": "36kr", "base_url": "https://36kr.com", "category": CATEGORY_AI, "interval": 120},
        {"name": "知乎", "code": "zhihu", "base_url": "https://www.zhihu.com", "category": CATEGORY_AI, "interval": 120},
    ]
    for ch_def in channel_defs:
        existing = session.query(Channel).filter(Channel.code == ch_def["code"]).first()
        if existing:
            channel_map[ch_def["code"]] = existing.id
        else:
            ch = Channel(
                name=ch_def["name"],
                code=ch_def["code"],
                base_url=ch_def["base_url"],
                category_id=category_map[ch_def["category"]],
                crawl_interval=ch_def["interval"],
                is_active=1,
            )
            session.add(ch)
            session.flush()
            channel_map[ch_def["code"]] = ch.id
            logger.info(f"创建渠道: {ch_def['name']}")
    session.commit()
    return channel_map


def init_mock_data(session, category_map: dict, channel_map: dict):
    """
    插入模拟数据，确保程序启动时有数据可查询
    参数:
        session: 数据库会话
        category_map: 分类映射
        channel_map: 渠道映射
    """
    existing_count = session.query(Info).count()
    if existing_count > 0:
        logger.info(f"已有{existing_count}条数据，跳过模拟数据插入")
        return

    now = datetime.now()
    mock_data = [
        # 热点事件
        {"source_id": "mock_wb_001", "title": "全国两会胜利闭幕", "content": "全国两会圆满闭幕，会议通过多项重要决议，涉及经济发展、民生改善等多个领域，为全年工作指明方向。今年两会重点讨论了GDP增长目标设定、财政赤字率安排、新质生产力培育等核心议题。代表委员们围绕扩大内需、促进就业、深化改革开放等提出大量建议，多项民生利好政策陆续出台，包括提高城乡居民收入、完善社会保障体系、推进教育公平等举措，为经济社会高质量发展注入强劲动力。", "channel_code": "weibo", "category_name": CATEGORY_HOT, "core_entity": "全国两会", "location": "北京"},
        {"source_id": "mock_wb_002", "title": "春季招聘市场持续升温", "content": "多地举办春季大型招聘会，人工智能、新能源等领域岗位需求旺盛，应届生就业形势总体向好。据人社部数据，今年春季招聘季全国累计举办线上线下招聘活动超过5万场，提供岗位信息超千万条。其中人工智能相关岗位同比增长超过80%，新能源、半导体、生物医药等战略性新兴产业招聘需求持续攀升。各地政府出台就业补贴、人才公寓等政策吸引青年人才，高校毕业生签约率较去年同期提升约5个百分点。", "channel_code": "weibo", "category_name": CATEGORY_HOT, "core_entity": "春季招聘", "location": "全国"},
        {"source_id": "mock_tt_001", "title": "新能源汽车销量再创新高", "content": "国内新能源汽车月度销量突破百万辆大关，渗透率持续提升，比亚迪、特斯拉等品牌表现亮眼。中汽协数据显示，新能源汽车单月销量达到102万辆，同比增长35%，市场渗透率首次突破40%。比亚迪以月销30万辆的成绩稳居榜首，特斯拉上海超级工厂出口量大幅增长。固态电池、800V高压平台等新技术加速落地，充电基础设施覆盖率持续提升，消费者对新能源汽车的接受度和购买意愿不断增强。", "channel_code": "toutiao", "category_name": CATEGORY_HOT, "core_entity": "新能源汽车", "location": "全国"},
        {"source_id": "mock_tt_002", "title": "文旅市场持续火爆", "content": "各地文旅市场持续火爆，特色小镇、乡村旅游成为新热点，文旅融合推动消费升级。文化和旅游部数据显示，国内旅游出游人次同比增长超过20%，旅游收入创历史同期新高。各地推出特色文旅产品，如沉浸式演艺、非遗体验、乡村民宿等，深受年轻游客青睐。多个网红城市凭借短视频平台出圈，带动当地餐饮、住宿、交通等产业链全面繁荣，文旅消费成为拉动内需的重要引擎。", "channel_code": "toutiao", "category_name": CATEGORY_HOT, "core_entity": "文旅市场", "location": "全国"},
        {"source_id": "mock_xhs_001", "title": "春日赏花攻略合集", "content": "全国多地进入赏花季，樱花、油菜花、桃花竞相绽放，各大公园和景区迎来客流高峰。武汉东湖樱花园、婺源油菜花海、林芝桃花沟等热门赏花地游客如织，周末单日客流量突破10万人次。各地推出夜赏灯光秀、花海音乐节、汉服游园等创新活动，赏花经济带动周边民宿、餐饮、文创产品销售大幅增长。气象部门提醒花粉过敏人群做好防护，建议错峰出行以获得更好体验。", "channel_code": "xiaohongshu", "category_name": CATEGORY_HOT, "core_entity": "赏花季", "location": "全国"},

        # 经济数据
        {"source_id": "mock_em_001", "title": "国际金价突破2400美元", "content": "受全球地缘政治风险和央行购金需求推动，国际金价持续走高，突破2400美元/盎司关口。全球央行连续两年净购金量超过1000吨，中国、印度等新兴经济体央行增持尤为明显。美联储降息预期升温，实际利率下行进一步支撑金价。分析师普遍认为，在全球不确定性加剧和去美元化趋势下，黄金作为避险资产的配置价值将持续凸显，年内有望挑战2500美元关口。", "channel_code": "eastmoney", "category_name": CATEGORY_ECONOMY, "core_entity": "国际金价", "indicator_name": "国际金价", "indicator_value": "2420.50美元/盎司"},
        {"source_id": "mock_em_002", "title": "国际原油价格震荡上行", "content": "OPEC+减产协议延续，叠加全球需求预期改善，国际原油价格震荡上行，布伦特原油突破85美元/桶。沙特和俄罗斯重申将维持自愿减产至年底，市场供应偏紧格局延续。中国经济复苏带动原油需求增长预期，美国战略石油储备补库需求也为油价提供支撑。不过市场也关注美国页岩油产量回升和全球能源转型加速对中长期油价的压制效应。", "channel_code": "eastmoney", "category_name": CATEGORY_ECONOMY, "core_entity": "国际原油", "indicator_name": "国际原油", "indicator_value": "85.30美元/桶"},
        {"source_id": "mock_em_003", "title": "人民币汇率稳中有升", "content": "美元人民币汇率报7.22，人民币汇率在合理均衡水平上保持基本稳定，跨境资金流动趋于平衡。央行通过多种货币政策工具维护外汇市场稳定，离岸人民币流动性管理机制不断完善。贸易顺差维持高位、外资持续流入中国债券市场等因素为人民币提供支撑。市场预期随着中美利差逐步收窄，人民币汇率有望进一步走强，年底可能测试7.0关口。", "channel_code": "eastmoney", "category_name": CATEGORY_ECONOMY, "core_entity": "美元人民币汇率", "indicator_name": "美元人民币汇率", "indicator_value": "7.22"},

        # 国际大事
        {"source_id": "mock_reu_001", "title": "联合国气候峰会达成新协议", "content": "联合国气候峰会闭幕，各国就减排目标达成新协议，承诺2030年前将碳排放量减少40%，并设立气候基金。协议首次将化石燃料转型纳入正式文本，要求各国制定逐步减少煤炭使用的具体时间表。发达国家承诺每年向发展中国家提供不低于1000亿美元的气候融资，用于可再生能源建设和气候适应项目。小岛屿国家联盟对协议表示谨慎欢迎，但认为减排力度仍不足以应对气候危机。", "channel_code": "reuters", "category_name": CATEGORY_INTERNATIONAL, "core_entity": "联合国", "location": "日内瓦"},
        {"source_id": "mock_reu_002", "title": "中东和平谈判取得进展", "content": "中东多方在开罗举行和平谈判，就停火和人道主义援助达成初步共识，国际社会表示欢迎。谈判各方同意在加沙地区实施为期6周的停火，允许人道主义援助物资进入，并启动被扣押人员交换程序。联合国秘书长呼吁各方切实履行承诺，美国、埃及、卡塔尔将继续作为调解方推动后续谈判。分析人士指出，虽然停火协议是积极信号，但持久和平仍面临诸多挑战。", "channel_code": "reuters", "category_name": CATEGORY_INTERNATIONAL, "core_entity": "中东和平", "location": "开罗"},
        {"source_id": "mock_reu_003", "title": "G7峰会关注全球供应链安全", "content": "G7领导人峰会聚焦全球供应链安全议题，讨论半导体、稀土等关键资源的供应链多元化策略。会议决定建立关键矿产储备机制，减少对单一供应国的依赖，并投入500亿美元支持成员国半导体制造能力建设。各方还就人工智能治理框架、跨境数据流动规则等新兴议题展开讨论，承诺加强协调合作应对技术脱钩风险。", "channel_code": "reuters", "category_name": CATEGORY_INTERNATIONAL, "core_entity": "G7", "location": "广岛"},

        # 科技动向
        {"source_id": "mock_csdn_001", "title": "Rust语言2024年度报告发布", "content": "Rust基金会发布2024年度报告，Rust语言在系统编程领域采用率持续增长，Linux内核集成Rust代码量翻倍。报告显示全球Rust开发者社区已超过300万人，企业级采用率同比增长45%。微软、谷歌、亚马逊等科技巨头在操作系统内核、网络协议栈、嵌入式系统等关键基础设施中加速引入Rust。Rust的安全特性有效减少了内存安全漏洞，成为替代C/C++的重要选择。", "channel_code": "csdn", "category_name": CATEGORY_TECH, "core_entity": "Rust语言"},
        {"source_id": "mock_csdn_002", "title": "量子计算突破千量子比特", "content": "IBM发布新一代量子处理器，量子比特数突破千位大关，量子纠错技术取得重大进展。IBM Quantum Heron处理器搭载1121个量子比特，采用模块化架构设计，支持多芯片互联扩展。谷歌、微软等公司也在量子纠错码和拓扑量子比特方面取得突破，量子计算正从实验室走向实用化。专家预测，未来3-5年内量子计算有望在药物发现、材料模拟、金融优化等领域实现商业化应用。", "channel_code": "csdn", "category_name": CATEGORY_TECH, "core_entity": "量子计算"},
        {"source_id": "mock_jj_001", "title": "WebAssembly 3.0规范正式发布", "content": "W3C正式发布WebAssembly 3.0规范，新增GC支持和组件模型，为Web应用性能带来质的飞跃。GC支持使得Rust、Kotlin等语言编译到Wasm时无需自行管理内存，大幅降低开发复杂度。组件模型定义了标准化的模块接口规范，解决了不同语言编译的Wasm模块之间的互操作性问题。Firefox、Chrome已率先实现核心特性支持，预计将推动游戏引擎、视频编辑、CAD等重型应用加速向Web端迁移。", "channel_code": "juejin", "category_name": CATEGORY_TECH, "core_entity": "WebAssembly"},
        {"source_id": "mock_jj_002", "title": "云原生架构最佳实践总结", "content": "基于Kubernetes的云原生架构最佳实践总结，涵盖微服务治理、服务网格、可观测性等核心领域。实践表明，采用Istio服务网格可实现流量管理、安全策略和可观测性的统一治理，降低微服务间通信复杂度。OpenTelemetry标准化的可观测性方案整合了日志、指标和链路追踪三大支柱，显著提升故障定位效率。Serverless与容器化混合部署模式在降本增效方面表现突出，资源利用率平均提升40%。", "channel_code": "juejin", "category_name": CATEGORY_TECH, "core_entity": "云原生"},
        {"source_id": "mock_cnb_001", "title": ".NET 9正式版发布", "content": "微软发布.NET 9正式版，性能大幅提升，新增原生AOT编译优化和AI开发工具链集成。基准测试显示.NET 9在HTTP吞吐量、JSON序列化和数据库访问等场景下性能提升15%-30%。原生AOT编译的应用启动时间缩短至毫秒级，内存占用减少50%，非常适合云原生和边缘计算场景。内置的Microsoft.Extensions.AI库提供了统一的AI服务抽象层，简化了大模型调用和向量搜索集成。", "channel_code": "cnblogs", "category_name": CATEGORY_TECH, "core_entity": ".NET 9"},

        # AI大模型动向
        {"source_id": "mock_36kr_001", "title": "GPT-5发布引发行业震动", "content": "OpenAI发布GPT-5模型，在推理能力、多模态理解和代码生成方面实现重大突破，AGI进程加速。GPT-5在数学推理基准GSM8K上达到97%准确率，较GPT-4提升15个百分点。多模态能力扩展至视频理解和实时语音交互，支持长达1小时的视频内容分析。代码生成方面，GPT-5在SWE-Bench基准测试中解决了62%的真实GitHub Issue，接近高级开发者水平。", "channel_code": "36kr", "category_name": CATEGORY_AI, "core_entity": "GPT-5"},
        {"source_id": "mock_36kr_002", "title": "国产大模型百花齐放", "content": "国内多家企业发布新一代大模型，文心一言、通义千问、Kimi等在各项基准测试中表现优异。百度文心4.5在中文理解和生成任务上超越GPT-4，阿里通义千问2.5开源版本在多项国际评测中名列前茅。月之暗面Kimi支持200万字超长上下文，在文档理解和长文本推理方面优势明显。国产大模型在中文场景下的表现已达到国际一流水平，生态建设加速推进。", "channel_code": "36kr", "category_name": CATEGORY_AI, "core_entity": "国产大模型"},
        {"source_id": "mock_zh_001", "title": "AI Agent技术路线深度解析", "content": "AI Agent成为大模型应用新范式，AutoGPT、MetaGPT等框架推动AI从对话走向自主决策和任务执行。AI Agent的核心架构包含规划、记忆、工具使用三大模块，通过思维链分解复杂任务，借助外部工具扩展能力边界。多Agent协作模式在软件开发、科研实验、企业运营等场景展现巨大潜力，MetaGPT模拟软件团队协作完成需求分析到代码生成的全流程。业界预计AI Agent将在2025年迎来规模化应用爆发。", "channel_code": "zhihu", "category_name": CATEGORY_AI, "core_entity": "AI Agent"},
        {"source_id": "mock_zh_002", "title": "多模态大模型技术演进", "content": "多模态大模型从图文理解走向视频生成，Sora等模型展示强大视频生成能力，视觉理解与生成统一架构成为趋势。OpenAI Sora可生成长达2分钟的高保真视频，在物理世界模拟方面表现惊人。谷歌Gemini 1.5 Pro支持百万级Token输入，实现跨模态长文档理解。国内智谱GLM-4.6V、字节PixelDance等模型也在视频生成领域取得突破，多模态大模型正重塑内容创作、影视制作、教育培训等行业。", "channel_code": "zhihu", "category_name": CATEGORY_AI, "core_entity": "多模态大模型"},
    ]

    for item in mock_data:
        channel_id = channel_map.get(item["channel_code"])
        category_id = category_map.get(item["category_name"])
        if not channel_id or not category_id:
            continue

        info = Info(
            source_id=item["source_id"],
            title=item["title"],
            content=item["content"],
            category_id=category_id,
            channel_id=channel_id,
            source_url=f"https://example.com/{item['source_id']}",
            event_time=now - timedelta(minutes=random.randint(10, 7200)),
            core_entity=item.get("core_entity", ""),
            location=item.get("location", ""),
            indicator_name=item.get("indicator_name", ""),
            indicator_value=item.get("indicator_value", ""),
            detail_fetch_status="success",
        )
        session.add(info)

    session.commit()
    logger.info(f"已插入{len(mock_data)}条模拟数据")


def init_all_data():
    """
    执行完整的数据初始化流程
    1. 创建数据库表结构
    2. 初始化分类数据
    3. 初始化渠道数据
    4. 插入模拟数据
    """
    init_db()

    session = get_session()
    try:
        category_map = init_categories(session)
        channel_map = init_channels(session, category_map)
        init_mock_data(session, category_map, channel_map)
        logger.info("数据初始化完成")
    except Exception as e:
        session.rollback()
        logger.error(f"数据初始化失败: {e}", exc_info=True)
        raise
    finally:
        session.close()
