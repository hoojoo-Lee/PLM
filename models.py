"""
PLM 数据模型 - EMS/ODM 客户项目模式
业务逻辑：产品 = 客户项目，被动接收客户 BOM，进行版本封存
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
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
# 产品层 (Product) - 客户项目
# =============================================================================

class Product(Base):
    """产品主表 - 最高层级，即客户项目"""
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True)
    name = Column(String(200), nullable=False, comment="产品名称/客户项目名称")
    code = Column(String(50), unique=True, nullable=False, comment="产品编码/项目编号")
    description = Column(Text, comment="产品描述/项目描述")
    status = Column(String(20), server_default=text("'active'"), comment="状态: active/inactive")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    projects = relationship("Project", back_populates="product", cascade="all, delete-orphan")
    bom_versions = relationship("BOMVersion", back_populates="product", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="product", cascade="all, delete-orphan")


# =============================================================================
# 项目层 (Project) - 内部执行项目
# =============================================================================

class Project(Base):
    """项目表 - 挂属于 Product，用于内部执行跟踪"""
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    project_code = Column(String(50), unique=True, nullable=False, comment="内部项目编码")
    name = Column(String(200), nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    
    phase = Column(String(30), server_default=text("'planning'"), comment="阶段: planning/design/prototype/validation/production/eol")
    status = Column(String(20), server_default=text("'active'"), comment="状态: active/on_hold/completed/cancelled")
    
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="projects")


# =============================================================================
# BOM 版本管理 (BOMVersion)
# =============================================================================

class BOMVersion(Base):
    """BOM 版本表 - 挂属于 Product，每次客户提供新 BOM 创建新版本"""
    __tablename__ = "bom_versions"
    __table_args__ = (
        UniqueConstraint("product_id", "version_code", name="uq_bom_version_product_code"),
    )

    id = Column(BigInteger, primary_key=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    version_code = Column(String(20), nullable=False, comment="版本号: V1/V2/V1.0/V2.1")
    status = Column(String(20), server_default=text("'active'"), comment="状态: active/archived")
    
    received_at = Column(DateTime(timezone=True), server_default=text("now()"), comment="客户提供 BOM 的时间")
    change_notes = Column(Text, comment="变更说明/客户备注")
    
    created_by = Column(String(100), comment="创建人/接收人")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))

    product = relationship("Product", back_populates="bom_versions")
    bom_items = relationship("BOMItem", back_populates="bom_version", cascade="all, delete-orphan")


# =============================================================================
# BOM 物料明细 (BOMItem)
# =============================================================================

class BOMItem(Base):
    """BOM 物料明细表 - 强关联 BOM_Version，支持独立版本控制"""
    __tablename__ = "bom_items"

    id = Column(BigInteger, primary_key=True)
    bom_version_id = Column(BigInteger, ForeignKey("bom_versions.id", ondelete="CASCADE"), nullable=False)

    category = Column(String(50), comment="分类: 结构件/组装辅件/PCBA/包装件/电子辅件")
    responsible_party = Column(String(50), nullable=True, default='', comment="责任方: 客户方/NexPCB")
    mpn = Column(String(100), comment="ERP料号")
    name = Column(String(200), nullable=False, comment="物料名称")
    quantity = Column(Integer, server_default=text("1"), comment="数量")

    responsible = Column(String(100), comment="责任人")
    status = Column(String(20), server_default=text("'pending'"), comment="状态: pending/review/approved/rejected")

    picture_drive_id = Column(String(200), comment="外观预览图标识")
    design_files = Column(JSON, default=list, comment="设计文件列表: [{file_type, drive_id, version}]")
    sort_order = Column(Integer, server_default=text("0"), comment="拖拽排序序号")

    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    bom_version = relationship("BOMVersion", back_populates="bom_items")
    documents = relationship("Document", back_populates="bom_item", cascade="all, delete-orphan")


# =============================================================================
# 文档管理 (Document) - 双层挂载
# =============================================================================

class Document(Base):
    """文档表 - 挂载于 Product、BOM_Item 或 BOM_Version"""
    __tablename__ = "documents"

    id = Column(BigInteger, primary_key=True)

    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    bom_item_id = Column(BigInteger, ForeignKey("bom_items.id", ondelete="SET NULL"), comment="为空则为产品级全局文件")
    bom_version_id = Column(BigInteger, ForeignKey("bom_versions.id", ondelete="SET NULL"), comment="挂载到 BOM 版本（ECN/底层 BOM 文件）")
    
    title = Column(String(300), nullable=False, comment="文档标题")
    document_type = Column(String(50), comment="类型: drawing/spec/test_report/certificate/package/manual")
    
    version = Column(String(20), server_default=text("'1'"), comment="版本号")
    received_date = Column(Date, server_default=text("CURRENT_DATE"), comment="客户下发/输入日期")
    google_drive_id = Column(String(100), nullable=True, comment="Google Drive 文件 ID")
    
    file_name = Column(String(255), comment="原始文件名")
    file_size = Column(BigInteger, comment="文件大小 (bytes)")
    mime_type = Column(String(100), comment="MIME 类型")
    
    status = Column(String(20), server_default=text("'draft'"), comment="draft/review/approved/released")
    update_notes = Column(Text, comment="更新说明")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="documents")
    bom_item = relationship("BOMItem", back_populates="documents")


# =============================================================================
# 变更日志 (ChangeLog) - 轻量化 ECN
# =============================================================================

class ChangeLog(Base):
    """变更日志 - 记录所有操作"""
    __tablename__ = "change_logs"

    id = Column(BigInteger, primary_key=True)
    
    entity_type = Column(String(30), nullable=False, comment="实体类型: Product/BOM/Doc")
    entity_id = Column(BigInteger, nullable=False, comment="实体主键")
    entity_name = Column(String(200), comment="实体名称")
    
    change_type = Column(String(20), nullable=False, comment="变更类型: create/update/delete/archive")
    change_summary = Column(Text, nullable=False, comment="变更说明")
    change_detail = Column(String(1000), comment="变更详情")
    
    changed_by = Column(String(100), comment="变更人")
    
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
