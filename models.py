"""
PLM 数据模型 - V4.0 架构方案
业务逻辑：产品 = 客户项目，被动接收客户 BOM，进行版本封存
核心规则：
- product_id 是系统唯一的数据挂载中心
- BOM 通过 bom_type + variant_tag 实现变体，不建 SKU 表
- 柔性防呆：Released BOM 允许编辑，后端静默记录 ChangeLog diff
- TrackerTask 与 GanttTask 通过 gantt_task_id 软关联
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from database import Base


# =============================================================================
# L0: 全局配置
# =============================================================================

class SysHoliday(Base):
    """系统节假日模型"""
    __tablename__ = "sys_holidays"

    date = Column(Date, primary_key=True, comment="节假日日期")
    note = Column(String(100), comment="节假日名称")


class NPICategory(Base):
    """NPI 分类模型 - 预置 39 条种子数据"""
    __tablename__ = "npi_categories"

    id = Column(BigInteger, primary_key=True, comment="Category ID")
    name = Column(String(200), nullable=False, comment="39个Category名称")
    description = Column(Text, comment="用途说明")
    applicable_stages = Column(String(100), comment="适用阶段: S0,S1,S2...")
    typical_task = Column(String(200), comment="典型Task示例")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))


# =============================================================================
# L1: 客户层
# =============================================================================

class Customer(Base):
    """客户表"""
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("name", name="uq_customers_name"),
    )

    id = Column(BigInteger, primary_key=True, comment="客户ID")
    name = Column(String(200), nullable=False, comment="客户名称")
    background = Column(Text, comment="客户背景信息")
    team_info = Column(Text, comment="客户团队描述")
    website = Column(String(200), comment="官网")
    industry = Column(String(100), comment="行业")
    company_scale = Column(String(50), comment="公司规模")
    location = Column(String(100), comment="所在地")
    pm_contact = Column(String(100), comment="PM对接人")
    contact_name = Column(String(100), nullable=True, comment="联系人")
    contact_email = Column(String(200), nullable=True, comment="联系邮箱")
    background_notes = Column(Text, nullable=True, comment="客户背景与特殊要求")
    status = Column(String(20), server_default=text("'active'"), comment="合作状态: active/inactive/archived")
    tier = Column(String(20), comment="客户等级")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    products = relationship("Product", back_populates="customer", cascade="all, delete-orphan")


# =============================================================================
# L2: 产品层
# =============================================================================

class Product(Base):
    """产品主表 - 最高层级，即客户项目"""
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("code", name="uq_products_code"),
    )

    id = Column(BigInteger, primary_key=True, comment="产品ID")
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, comment="归属客户ID")
    
    name = Column(String(200), nullable=False, comment="产品名称/客户项目名称")
    code = Column(String(50), unique=True, nullable=True, comment="产品编码/项目编号")
    description = Column(Text, comment="产品描述/项目描述")
    usage_scenario = Column(Text, comment="产品使用场景")
    key_ic_info = Column(Text, comment="关键IC信息")
    
    lifecycle_stage = Column(String(20), server_default=text("'S0'"), comment="生命周期: S0-S6")
    lifecycle_history = Column(JSON, default=list, comment="阶段流转历史")
    core_concern = Column(String(200), comment="核心关切")
    annual_workload = Column(Text, comment="年度工作量预估")
    
    status = Column(String(20), server_default=text("'active'"), comment="状态: active/inactive/archived")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="products")
    projects = relationship("Project", back_populates="product", cascade="all, delete-orphan")
    bom_versions = relationship("BOMVersion", back_populates="product", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="product", cascade="all, delete-orphan")
    orders = relationship("ProductOrder", back_populates="product", cascade="all, delete-orphan")
    risks = relationship("Risk", back_populates="product", cascade="all, delete-orphan")


# =============================================================================
# L2.5: 产品订单
# =============================================================================

class ProductOrder(Base):
    """产品订单表"""
    __tablename__ = "product_orders"

    id = Column(BigInteger, primary_key=True, comment="订单ID")
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, comment="所属产品ID")
    
    order_code = Column(String(50), nullable=False, comment="订单编号")
    description = Column(Text, comment="订单描述")
    quantity = Column(Integer, server_default=text("1"), comment="数量")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="交付日期")
    status = Column(String(20), server_default=text("'ongoing'"), comment="状态: ongoing/delivered/cancelled")
    notes = Column(Text, comment="备注")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="orders")


# =============================================================================
# L3-A: BOM 版本管理
# =============================================================================

class BOMVersion(Base):
    """BOM 版本表 - 挂属于 Product，variant_tag 替代 SKU"""
    __tablename__ = "bom_versions"
    __table_args__ = (
        UniqueConstraint("product_id", "bom_type", "variant_tag", name="uq_bom_version_product_type_variant"),
    )

    id = Column(BigInteger, primary_key=True, comment="BOM版本ID")
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, comment="所属产品ID")
    
    version_code = Column(String(20), nullable=False, comment="版本号: V1/V2.1/rev B1")
    bom_type = Column(String(20), server_default=text("'EE'"), comment="BOM类型: EE/ME/PKG")
    variant_tag = Column(String(50), server_default=text("'DEFAULT'"), comment="SKU变体标签: DEFAULT/TRUFFLE-CASE/...")
    status = Column(String(20), server_default=text("'active'"), comment="状态: draft/active/released/archived")
    
    type_specific_fields = Column(JSON, default=dict, comment="版本级专有字段(JSONB)")
    change_notes = Column(Text, comment="变更说明/客户备注")
    created_by = Column(String(100), comment="创建人/接收人")
    released_at = Column(DateTime(timezone=True), comment="发布时间")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))

    product = relationship("Product", back_populates="bom_versions")
    bom_items = relationship("BOMItem", back_populates="bom_version", cascade="all, delete-orphan")


# =============================================================================
# L3-B: BOM 物料明细
# =============================================================================

class BOMItem(Base):
    """BOM 物料明细表 - 强关联 BOM_Version"""
    __tablename__ = "bom_items"

    id = Column(BigInteger, primary_key=True, comment="物料ID")
    bom_version_id = Column(BigInteger, ForeignKey("bom_versions.id", ondelete="CASCADE"), nullable=False, comment="所属BOM版本ID")

    category = Column(String(50), comment="物料分类")
    responsible_party = Column(String(50), default='', comment="责任方: 客户方/NexPCB")
    mpn = Column(String(100), comment="MPN/制造商料号")
    internal_pn = Column(String(100), comment="内部料号")
    name = Column(String(200), nullable=False, comment="物料名称")
    quantity = Column(Integer, server_default=text("1"), comment="数量")

    responsible = Column(String(100), comment="责任人")
    design_finalization = Column(String(50), comment="设计定型")
    
    picture_drive_id = Column(String(200), comment="外观预览图标识")
    design_files = Column(JSON, default=list, comment="设计文件列表")
    item_specific_data = Column(JSON, default=dict, comment="Item级专有字段(JSONB)")
    
    sample_no = Column(String(50), comment="样品编号")
    qc_sample = Column(Boolean, server_default=text("false"), comment="QC样品")
    standard = Column(Boolean, server_default=text("false"), comment="标准件")
    comments = Column(Text, comment="备注")
    
    lead_time_s1 = Column(String(20), comment="S1交期")
    lead_time_s2 = Column(String(20), comment="S2交期")
    lead_time_s3 = Column(String(20), comment="S3交期")
    
    sort_order = Column(Integer, server_default=text("0"), comment="拖拽排序序号")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    bom_version = relationship("BOMVersion", back_populates="bom_items")
    documents = relationship("Document", back_populates="bom_item", cascade="all, delete-orphan")


# =============================================================================
# L4: 项目层
# =============================================================================

class Project(Base):
    """项目表 - 挂属于 Product，用于内部执行跟踪"""
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, comment="项目ID")
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, comment="所属产品ID")
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, comment="所属客户ID")
    
    name = Column(String(200), nullable=False, comment="项目名称")
    code = Column(String(50), unique=True, nullable=False, comment="项目编码")
    
    sales = Column(String(100), comment="销售负责人")
    pm = Column(String(100), comment="PM负责人")
    ee = Column(String(100), comment="EE负责人")
    me = Column(String(100), comment="ME负责人")
    
    current_stage = Column(String(20), server_default=text("'S0'"), comment="当前阶段: S0-S6")
    goal = Column(Text, comment="项目目标")
    control_book_link = Column(String(200), comment="Control Book链接")
    basecamp_url = Column(String(500), nullable=True, comment="项目链接(Basecamp等)")
    
    status = Column(String(20), server_default=text("'active'"), comment="状态: active/completed/hold/cancelled")
    start_date = Column(Date, comment="开始日期")
    target_mp_date = Column(Date, comment="目标量产日期")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="projects")


# =============================================================================
# L6: 文控中心（父子表）
# =============================================================================

class Document(Base):
    """文档表 - 逻辑主体"""
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True, comment="文档ID")
    
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, comment="所属产品ID")
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, comment="关联项目ID")
    bom_item_id = Column(BigInteger, ForeignKey("bom_items.id", ondelete="SET NULL"), nullable=True, comment="关联物料ID")
    
    title = Column(String(300), nullable=False, comment="文档标题")
    document_type = Column(String(50), comment="类型")
    category = Column(String(50), comment="子分类")
    status = Column(String(20), server_default=text("'active'"), comment="状态: active/archived")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="documents")
    bom_item = relationship("BOMItem", back_populates="documents")


class DocumentVersion(Base):
    """文档版本表 - 物理文件版本"""
    __tablename__ = "document_versions"

    id = Column(BigInteger, primary_key=True, comment="版本ID")
    document_id = Column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, comment="所属文档ID")
    
    version_number = Column(String(20), server_default=text("'1'"), comment="版本号: V1/V2/rev A")
    received_date = Column(Date, server_default=text("CURRENT_DATE"), comment="下发日期")
    google_drive_id = Column(String(100), nullable=True, comment="Google Drive文件ID")
    
    file_name = Column(String(255), comment="原始文件名")
    file_size = Column(BigInteger, comment="文件大小")
    mime_type = Column(String(100), comment="MIME类型")
    
    responsible = Column(String(100), comment="负责人")
    status = Column(String(20), server_default=text("'draft'"), comment="状态: draft/released")
    update_notes = Column(Text, comment="更新说明")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))


# =============================================================================
# L7: 变更日志（全局，吸收 ECN 功能）
# =============================================================================

class ChangeLog(Base):
    """变更日志 - 记录所有操作"""
    __tablename__ = "change_logs"

    id = Column(BigInteger, primary_key=True, comment="日志ID")
    
    entity_type = Column(String(30), nullable=False, comment="实体类型: Product/BOM/Doc/Order/Project")
    entity_id = Column(BigInteger, nullable=False, comment="实体主键")
    entity_name = Column(String(200), comment="实体名称")
    
    change_type = Column(String(20), nullable=False, comment="变更类型: create/update/delete/archive")
    source = Column(String(20), server_default=text("'manual'"), comment="变更来源: manual/excel_import/rollback")
    
    change_summary = Column(Text, nullable=False, comment="变更说明")
    change_detail = Column(JSON, default=list, comment="变更详情(含old/new diff): [{field, old_value, new_value}]")
    
    changed_by = Column(String(100), comment="变更人")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))


# =============================================================================
# 甘特图任务（保留现有，后续 Phase 2 调整）
# =============================================================================

class GanttTask(Base):
    """甘特图任务模型"""
    __tablename__ = "gantt_tasks"

    id = Column(BigInteger, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    task_text = Column(String(200), nullable=False, comment="任务名称")
    start_date = Column(Date, nullable=False, comment="开始日期")
    end_date = Column(Date, nullable=False, comment="结束日期")
    duration = Column(Integer, default=1, comment="持续天数")
    is_workday_only = Column(Boolean, default=False, comment="是否仅工作日")
    progress = Column(Float, default=0, comment="进度 0-1")
    dependencies = Column(String(500), default="", comment="紧前依赖任务ID")
    assignee = Column(String(100), default="", comment="负责人")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))


class TaskTemplate(Base):
    """任务模板模型"""
    __tablename__ = "task_templates"

    id = Column(BigInteger, primary_key=True)
    name = Column(String(200), nullable=False, comment="模板名称")
    default_duration = Column(Integer, default=1, comment="默认持续天数")


class TrackerTask(Base):
    """NPI Tracker 任务表"""
    __tablename__ = "tracker_tasks"

    id = Column(BigInteger, primary_key=True, comment="任务ID")
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, comment="关联项目ID")
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, comment="所属产品ID")
    category_id = Column(BigInteger, ForeignKey("npi_categories.id", ondelete="SET NULL"), nullable=True, comment="NPI分类ID")
    gantt_task_id = Column(BigInteger, ForeignKey("gantt_tasks.id", ondelete="SET NULL"), nullable=True, comment="关联甘特图任务ID")

    stage = Column(String(20), comment="阶段: proto/dvt/pvt/mp")
    task_description = Column(String(500), nullable=False, comment="任务描述")
    function = Column(String(50), comment="职能")
    owner = Column(String(100), comment="负责人")
    priority = Column(String(10), server_default=text("'P2'"), comment="优先级: P0/P1/P2/P3")
    
    start_date = Column(Date, comment="计划开始日期")
    deadline = Column(Date, comment="截止日期")
    planned_days = Column(Integer, comment="计划天数")
    actual_date = Column(Date, comment="实际完成日期")
    delay_days = Column(Integer, server_default=text("0"), comment="延期天数")
    
    status = Column(String(20), server_default=text("'pending'"), comment="状态: pending/in_progress/done/blocked")
    risk_flag = Column(Boolean, server_default=text("false"), comment="风险标记")
    
    checklist = Column(JSON, default=list, comment="检查项")
    notes = Column(Text, comment="备注")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    product = relationship("Product", backref="tracker_tasks")


class Risk(Base):
    """风险表"""
    __tablename__ = "risks"

    id = Column(BigInteger, primary_key=True, comment="风险ID")
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, comment="所属产品ID")
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, comment="关联项目ID")

    category = Column(String(50), comment="风险类别")
    title = Column(String(200), nullable=False, comment="风险标题")
    description = Column(Text, comment="风险描述")
    mitigation_plan = Column(Text, comment="缓解措施")
    
    risk_level = Column(String(20), server_default=text("'medium'"), comment="风险等级: low/medium/high/critical")
    risk_type = Column(String(50), comment="风险类型")
    
    status = Column(String(20), server_default=text("'open'"), comment="状态: open/monitoring/resolved/closed")
    
    start_date = Column(Date, comment="识别日期")
    end_date = Column(Date, comment="预计解决日期")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="risks")
