"""
PLM Pydantic 验证模型 - EMS/ODM 客户项目模式
"""

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}


class TimestampSchema(BaseSchema):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# 产品 (Product)
# =============================================================================

class ProductBase(BaseSchema):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    status: str = Field(default="active")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    status: Optional[str] = None


class ProductResponse(ProductBase, TimestampSchema):
    id: int


class ProductBrief(BaseSchema):
    id: int
    name: str
    code: str
    status: str


# =============================================================================
# 项目 (Project)
# =============================================================================

class ProjectBase(BaseSchema):
    product_id: int
    project_code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    phase: str = Field(default="planning")
    status: str = Field(default="active")
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseSchema):
    product_id: Optional[int] = None
    project_code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    phase: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(ProjectBase, TimestampSchema):
    id: int


class ProjectBrief(BaseSchema):
    id: int
    project_code: str
    name: str
    phase: str
    status: str


# =============================================================================
# BOM 版本 (BOMVersion)
# =============================================================================

class BOMVersionBase(BaseSchema):
    product_id: int
    version_code: str = Field(..., max_length=20)
    status: str = Field(default="active")
    received_at: Optional[datetime] = None
    change_notes: Optional[str] = None
    created_by: Optional[str] = Field(None, max_length=100)


class BOMVersionCreate(BOMVersionBase):
    pass


class BOMVersionUpdate(BaseSchema):
    product_id: Optional[int] = None
    version_code: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = None
    received_at: Optional[datetime] = None
    change_notes: Optional[str] = None
    created_by: Optional[str] = Field(None, max_length=100)


class BOMVersionResponse(BOMVersionBase):
    id: int
    created_at: datetime


class BOMVersionBrief(BaseSchema):
    id: int
    version_code: str
    status: str
    received_at: datetime


# =============================================================================
# BOM 物料明细 (BOMItem)
# =============================================================================

class BOMItemBase(BaseSchema):
    bom_version_id: int
    category: Optional[str] = Field(None, max_length=50)
    mpn: Optional[str] = Field(None, max_length=100)
    name: str = Field(..., max_length=200)
    quantity: int = Field(default=1, ge=0)
    designator: Optional[str] = Field(None, max_length=100)
    responsible: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="pending")
    picture_drive_id: Optional[str] = Field(None, max_length=100)


class BOMItemCreate(BOMItemBase):
    pass


class BOMItemUpdate(BaseSchema):
    bom_version_id: Optional[int] = None
    category: Optional[str] = Field(None, max_length=50)
    mpn: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=200)
    quantity: Optional[int] = Field(None, ge=0)
    designator: Optional[str] = Field(None, max_length=100)
    responsible: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    picture_drive_id: Optional[str] = Field(None, max_length=100)


class BOMItemResponse(BOMItemBase, TimestampSchema):
    id: int


class BOMItemBrief(BaseSchema):
    id: int
    category: Optional[str] = None
    mpn: Optional[str] = None
    name: str
    quantity: int
    status: str


# =============================================================================
# 文档 (Document)
# =============================================================================

class DocumentBase(BaseSchema):
    product_id: int
    bom_item_id: Optional[int] = None
    title: str = Field(..., max_length=300)
    document_type: Optional[str] = Field(None, max_length=50)
    version: str = Field(default="1", max_length=20)
    google_drive_id: str = Field(..., max_length=100)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="draft")
    update_notes: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseSchema):
    product_id: Optional[int] = None
    bom_item_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=300)
    document_type: Optional[str] = Field(None, max_length=50)
    version: Optional[str] = Field(None, max_length=20)
    google_drive_id: Optional[str] = Field(None, max_length=100)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = None
    update_notes: Optional[str] = None


class DocumentResponse(DocumentBase, TimestampSchema):
    id: int


class DocumentBrief(BaseSchema):
    id: int
    title: str
    document_type: Optional[str] = None
    version: str
    status: str


# =============================================================================
# 变更日志 (ChangeLog)
# =============================================================================

class ChangeLogBase(BaseSchema):
    entity_type: str = Field(..., max_length=30)
    entity_id: int
    entity_name: Optional[str] = Field(None, max_length=200)
    change_type: str = Field(..., max_length=20)
    change_summary: str
    change_detail: Optional[str] = Field(None, max_length=1000)
    changed_by: Optional[str] = Field(None, max_length=100)


class ChangeLogCreate(ChangeLogBase):
    pass


class ChangeLogResponse(ChangeLogBase):
    id: int
    created_at: datetime


# =============================================================================
# 聚合响应
# =============================================================================

class ProductDetailResponse(ProductResponse):
    projects: list[ProjectBrief] = []
    bom_versions: list[BOMVersionBrief] = []
    documents: list[DocumentBrief] = []


class BOMVersionDetailResponse(BOMVersionResponse):
    bom_items: list[BOMItemBrief] = []


class BOMItemDetailResponse(BOMItemResponse):
    documents: list[DocumentBrief] = []
