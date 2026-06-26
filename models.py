from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from database import Base


class Project(Base):
    __tablename__ = "project"
    __table_args__ = {"comment": "项目主表"}

    id = Column(BigInteger, primary_key=True)
    project_code = Column(String, nullable=False, unique=True, comment="项目唯一编码")
    name = Column(String, nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    status = Column(String, nullable=False, server_default=text("'active'"), comment="项目状态")
    start_date = Column(Date, comment="项目开始日期")
    end_date = Column(Date, comment="项目结束日期")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="更新时间")

    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")
    parts = relationship("Part", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    timelines = relationship("Timeline", back_populates="project", cascade="all, delete-orphan")
    change_logs = relationship("ChangeLog", back_populates="project")


class Issue(Base):
    __tablename__ = "issue"
    __table_args__ = {"comment": "质量/缺陷追踪表"}

    id = Column(BigInteger, primary_key=True)
    project_id = Column(BigInteger, ForeignKey("project.id", ondelete="CASCADE"), nullable=False, comment="关联的项目")
    issue_key = Column(String, nullable=False, comment="项目内 Issue 唯一编号")
    issue_type = Column(String, nullable=False, comment="缺陷类型")
    summary = Column(Text, nullable=False, comment="缺陷摘要")
    description = Column(Text, comment="缺陷描述")
    status = Column(String, nullable=False, server_default=text("'open'"), comment="缺陷处理状态")
    priority = Column(String, comment="优先级")
    reported_by = Column(String, comment="报告者")
    assigned_to = Column(String, comment="指派人")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="更新时间")

    project = relationship("Project", back_populates="issues")
    change_logs = relationship("ChangeLog", back_populates="issue")


class Part(Base):
    __tablename__ = "part"
    __table_args__ = {"comment": "物料主数据表（扁平化管理）"}

    id = Column(BigInteger, primary_key=True)
    project_id = Column(BigInteger, ForeignKey("project.id", ondelete="SET NULL"), comment="关联的项目")
    part_code = Column(String, nullable=False, unique=True, comment="物料唯一编码")
    name = Column(String, nullable=False, comment="物料名称")
    revision = Column(String, comment="物料修订号")
    category = Column(String, comment="物料分类，例如 EE/ME/PKG")
    unit = Column(String, comment="计量单位")
    picture_drive_id = Column(String, comment="预览图片的 Google Drive 文件 ID")
    status = Column(String, nullable=False, server_default=text("'draft'"), comment="物料定型状态")
    description = Column(Text, comment="物料描述")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="更新时间")

    project = relationship("Project", back_populates="parts")
    documents = relationship("Document", back_populates="part", cascade="all, delete-orphan")
    change_logs = relationship("ChangeLog", back_populates="part")


class Timeline(Base):
    __tablename__ = "timeline"
    __table_args__ = {"comment": "项目进度时间线表"}

    id = Column(BigInteger, primary_key=True)
    project_id = Column(BigInteger, ForeignKey("project.id", ondelete="CASCADE"), nullable=False, comment="关联的项目")
    title = Column(String, nullable=False, comment="节点标题")
    description = Column(Text, comment="节点描述")
    due_date = Column(Date, comment="节点预计完成日期")
    status = Column(String, nullable=False, server_default=text("'pending'"), comment="节点状态")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="更新时间")

    project = relationship("Project", back_populates="timelines")


class Document(Base):
    __tablename__ = "document"
    __table_args__ = {"comment": "图纸/规格书管理表"}

    id = Column(BigInteger, primary_key=True)
    project_id = Column(BigInteger, ForeignKey("project.id", ondelete="SET NULL"), comment="关联的项目")
    part_id = Column(BigInteger, ForeignKey("part.id", ondelete="SET NULL"), comment="关联的物料")
    document_type = Column(String, comment="文档类型")
    title = Column(String, nullable=False, comment="文档标题")
    google_drive_file_id = Column(String, nullable=False, comment="Google Drive 文件 ID")
    version = Column(String, nullable=False, server_default=text("'1'"), comment="文档版本")
    update_notes = Column(Text, comment="更新说明")
    file_name = Column(String, comment="原始文件名")
    status = Column(String, nullable=False, server_default=text("'draft'"), comment="文档状态")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="更新时间")

    project = relationship("Project", back_populates="documents")
    part = relationship("Part", back_populates="documents")
    change_logs = relationship("ChangeLog", back_populates="document")


class ChangeLog(Base):
    __tablename__ = "change_log"
    __table_args__ = {"comment": "变更流水表，用于自动记录实体增删改差异"}

    id = Column(BigInteger, primary_key=True)
    project_id = Column(BigInteger, ForeignKey("project.id", ondelete="SET NULL"), comment="关联的项目")
    issue_id = Column(BigInteger, ForeignKey("issue.id", ondelete="SET NULL"), comment="关联的 Issue")
    part_id = Column(BigInteger, ForeignKey("part.id", ondelete="SET NULL"), comment="关联的物料")
    document_id = Column(BigInteger, ForeignKey("document.id", ondelete="SET NULL"), comment="关联的文档")
    entity_type = Column(String, nullable=False, comment="变更实体类型")
    entity_key = Column(String, comment="实体唯一标识")
    change_type = Column(String, nullable=False, comment="变更类型（create/update/delete）")
    diff = Column(JSONB, nullable=False, comment="存储变更前后差异的 JSONB 数据")
    comment = Column(Text, comment="变更说明")
    changed_by = Column(String, comment="变更用户")
    changed_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"), comment="变更时间")

    project = relationship("Project", back_populates="change_logs")
    issue = relationship("Issue", back_populates="change_logs")
    part = relationship("Part", back_populates="change_logs")
    document = relationship("Document", back_populates="change_logs")
