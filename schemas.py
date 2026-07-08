"""
PLM Pydantic 验证模型 - V4.0 架构方案
"""

from datetime import date, datetime
from typing import Any, Optional, Annotated

from pydantic import BaseModel, Field, BeforeValidator


def empty_str_to_none(v: Any) -> Any:
    if v == "" or v == "null" or v == "undefined":
        return None
    return v


OptionalDate = Annotated[Optional[date], BeforeValidator(empty_str_to_none)]


class BaseSchema(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}


class TimestampSchema(BaseSchema):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# 全局配置
# =============================================================================

class SysHolidayBase(BaseSchema):
    date: date
    note: Optional[str] = Field(None, max_length=100)


class SysHolidayCreate(SysHolidayBase):
    pass


class SysHolidayResponse(SysHolidayBase):
    pass


class NPICategoryBase(BaseSchema):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    applicable_stages: Optional[str] = Field(None, max_length=100)
    typical_task: Optional[str] = Field(None, max_length=200)


class NPICategoryCreate(NPICategoryBase):
    pass


class NPICategoryResponse(NPICategoryBase, TimestampSchema):
    id: int


class TaskTemplateBase(BaseSchema):
    name: str = Field(..., max_length=200)
    default_duration: int = Field(default=1, ge=1)


class TaskTemplateCreate(TaskTemplateBase):
    pass


class TaskTemplateResponse(TaskTemplateBase):
    id: int


# =============================================================================
# 客户 (Customer)
# =============================================================================

class CustomerBase(BaseSchema):
    name: str = Field(..., max_length=200)
    background: Optional[str] = None
    team_info: Optional[str] = None
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    company_scale: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    pm_contact: Optional[str] = Field(None, max_length=100)
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=200)
    background_notes: Optional[str] = None
    status: str = Field(default="active", max_length=20)
    tier: Optional[str] = Field(None, max_length=20)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=200)
    background: Optional[str] = None
    team_info: Optional[str] = None
    website: Optional[str] = Field(None, max_length=200)
    industry: Optional[str] = Field(None, max_length=100)
    company_scale: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    pm_contact: Optional[str] = Field(None, max_length=100)
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=200)
    background_notes: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    tier: Optional[str] = Field(None, max_length=20)


class CustomerResponse(CustomerBase, TimestampSchema):
    id: int


class CustomerBrief(BaseSchema):
    id: int
    name: str
    status: str
    tier: Optional[str] = None


# =============================================================================
# 产品 (Product)
# =============================================================================

class ProductBase(BaseSchema):
    name: str = Field(..., max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    usage_scenario: Optional[str] = None
    key_ic_info: Optional[str] = None
    lifecycle_stage: str = Field(default="S0", max_length=20)
    lifecycle_history: Optional[list[dict]] = Field(default_factory=list)
    core_concern: Optional[str] = Field(None, max_length=200)
    annual_workload: Optional[str] = None
    status: str = Field(default="active", max_length=20)


class ProductCreate(ProductBase):
    customer_id: Optional[int] = None


class ProductUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    usage_scenario: Optional[str] = None
    key_ic_info: Optional[str] = None
    lifecycle_stage: Optional[str] = Field(None, max_length=20)
    lifecycle_history: Optional[list[dict]] = None
    core_concern: Optional[str] = Field(None, max_length=200)
    annual_workload: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)


class ProductResponse(ProductBase, TimestampSchema):
    id: int
    customer_id: Optional[int] = None


class ProductBrief(BaseSchema):
    id: int
    name: str
    code: Optional[str] = None
    status: str
    lifecycle_stage: str


# =============================================================================
# 产品订单 (ProductOrder)
# =============================================================================

class ProductOrderBase(BaseSchema):
    order_code: str = Field(..., max_length=50)
    description: Optional[str] = None
    quantity: int = Field(default=1, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = Field(default="ongoing", max_length=20)
    notes: Optional[str] = None


class ProductOrderCreate(ProductOrderBase):
    pass


class ProductOrderUpdate(BaseSchema):
    order_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=1)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class ProductOrderResponse(ProductOrderBase, TimestampSchema):
    id: int
    product_id: int


class ProductOrderBrief(BaseSchema):
    id: int
    order_code: str
    quantity: int
    status: str
    end_date: Optional[date] = None


# =============================================================================
# BOM 版本 (BOMVersion)
# =============================================================================

class BOMVersionBase(BaseSchema):
    version_code: str = Field(..., max_length=20)
    bom_type: str = Field(default="EE", max_length=20)
    variant_tag: str = Field(default="DEFAULT", max_length=50)
    status: str = Field(default="active", max_length=20)
    type_specific_fields: Optional[dict[str, Any]] = Field(default_factory=dict)
    change_notes: Optional[str] = None
    created_by: Optional[str] = Field(None, max_length=100)
    released_at: Optional[datetime] = None


class BOMVersionCreate(BOMVersionBase):
    pass


class BOMVersionUpdate(BaseSchema):
    version_code: Optional[str] = Field(None, max_length=20)
    bom_type: Optional[str] = Field(None, max_length=20)
    variant_tag: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    type_specific_fields: Optional[dict[str, Any]] = None
    change_notes: Optional[str] = None
    created_by: Optional[str] = Field(None, max_length=100)
    released_at: Optional[datetime] = None


class BOMVersionResponse(BOMVersionBase, TimestampSchema):
    id: int
    product_id: int


class BOMVersionBrief(BaseSchema):
    id: int
    version_code: str
    bom_type: str
    variant_tag: str
    status: str


# =============================================================================
# BOM 物料明细 (BOMItem)
# =============================================================================

class BOMItemBase(BaseSchema):
    category: Optional[str] = Field(None, max_length=50)
    responsible_party: str = Field(default="NexPCB", max_length=50)
    mpn: Optional[str] = Field(None, max_length=100)
    internal_pn: Optional[str] = Field(None, max_length=100)
    name: str = Field(..., max_length=200)
    quantity: int = Field(default=1, ge=0)
    responsible: Optional[str] = Field(None, max_length=100)
    design_finalization: Optional[str] = Field(None, max_length=50)
    picture_drive_id: Optional[str] = Field(None, max_length=200)
    design_files: Optional[list[dict[str, Any]]] = Field(default_factory=list)
    item_specific_data: Optional[dict[str, Any]] = Field(default_factory=dict)
    sample_no: Optional[str] = Field(None, max_length=50)
    qc_sample: bool = Field(default=False)
    standard: bool = Field(default=False)
    comments: Optional[str] = None
    lead_time_s1: Optional[str] = Field(None, max_length=20)
    lead_time_s2: Optional[str] = Field(None, max_length=20)
    lead_time_s3: Optional[str] = Field(None, max_length=20)
    sort_order: int = Field(default=0)


class BOMItemCreate(BOMItemBase):
    pass


class BOMItemUpdate(BaseSchema):
    category: Optional[str] = Field(None, max_length=50)
    responsible_party: Optional[str] = Field(None, max_length=50)
    mpn: Optional[str] = Field(None, max_length=100)
    internal_pn: Optional[str] = Field(None, max_length=100)
    name: Optional[str] = Field(None, max_length=200)
    quantity: Optional[int] = Field(None, ge=0)
    responsible: Optional[str] = Field(None, max_length=100)
    design_finalization: Optional[str] = Field(None, max_length=50)
    picture_drive_id: Optional[str] = Field(None, max_length=200)
    design_files: Optional[list[dict[str, Any]]] = None
    item_specific_data: Optional[dict[str, Any]] = None
    sample_no: Optional[str] = Field(None, max_length=50)
    qc_sample: Optional[bool] = None
    standard: Optional[bool] = None
    comments: Optional[str] = None
    lead_time_s1: Optional[str] = Field(None, max_length=20)
    lead_time_s2: Optional[str] = Field(None, max_length=20)
    lead_time_s3: Optional[str] = Field(None, max_length=20)
    sort_order: Optional[int] = None


class BOMItemResponse(BOMItemBase, TimestampSchema):
    id: int
    bom_version_id: int


class BOMItemBrief(BaseSchema):
    id: int
    category: Optional[str] = None
    mpn: Optional[str] = None
    name: str
    quantity: int


# =============================================================================
# 项目 (Project)
# =============================================================================

class ProjectBase(BaseSchema):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=50)
    sales: Optional[str] = Field(None, max_length=100)
    pm: Optional[str] = Field(None, max_length=100)
    ee: Optional[str] = Field(None, max_length=100)
    me: Optional[str] = Field(None, max_length=100)
    current_stage: str = Field(default="S0", max_length=20)
    goal: Optional[str] = None
    control_book_link: Optional[str] = Field(None, max_length=200)
    basecamp_url: Optional[str] = Field(None, max_length=500)
    status: str = Field(default="active", max_length=20)
    start_date: Optional[date] = None
    target_mp_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    customer_id: Optional[int] = None


class ProjectUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=50)
    sales: Optional[str] = Field(None, max_length=100)
    pm: Optional[str] = Field(None, max_length=100)
    ee: Optional[str] = Field(None, max_length=100)
    me: Optional[str] = Field(None, max_length=100)
    current_stage: Optional[str] = Field(None, max_length=20)
    goal: Optional[str] = None
    control_book_link: Optional[str] = Field(None, max_length=200)
    basecamp_url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=20)
    start_date: Optional[date] = None
    target_mp_date: Optional[date] = None


class ProjectResponse(ProjectBase, TimestampSchema):
    id: int
    product_id: int


class ProjectBrief(BaseSchema):
    id: int
    code: str
    name: str
    current_stage: str
    status: str


# =============================================================================
# 文档 (Document) - 逻辑主体
# =============================================================================

class DocumentBase(BaseSchema):
    title: str = Field(..., max_length=300)
    document_type: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    status: str = Field(default="active", max_length=20)


class DocumentCreate(DocumentBase):
    project_id: Optional[int] = None
    bom_item_id: Optional[int] = None


class DocumentUpdate(BaseSchema):
    title: Optional[str] = Field(None, max_length=300)
    document_type: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)


class DocumentResponse(DocumentBase, TimestampSchema):
    id: int
    product_id: int


class DocumentBrief(BaseSchema):
    id: int
    title: str
    document_type: Optional[str] = None
    category: Optional[str] = None
    status: str


# =============================================================================
# 文档版本 (DocumentVersion) - 物理文件版本
# =============================================================================

class DocumentVersionBase(BaseSchema):
    version_number: str = Field(default="1", max_length=20)
    received_date: Optional[date] = None
    google_drive_id: Optional[str] = Field(None, max_length=100)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    responsible: Optional[str] = Field(None, max_length=100)
    status: str = Field(default="draft", max_length=20)
    update_notes: Optional[str] = None


class DocumentVersionCreate(DocumentVersionBase):
    pass


class DocumentVersionUpdate(BaseSchema):
    version_number: Optional[str] = Field(None, max_length=20)
    received_date: Optional[date] = None
    google_drive_id: Optional[str] = Field(None, max_length=100)
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)
    responsible: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=20)
    update_notes: Optional[str] = None


class DocumentVersionResponse(DocumentVersionBase, TimestampSchema):
    id: int
    document_id: int


# =============================================================================
# 甘特图任务 (GanttTask)
# =============================================================================

class GanttTaskBase(BaseSchema):
    task_text: str = Field(..., max_length=200)
    start_date: date
    end_date: date
    duration: int = Field(default=1, ge=1)
    is_workday_only: bool = Field(default=False)
    progress: float = Field(default=0.0, ge=0, le=1)
    dependencies: str = Field(default="")
    assignee: Optional[str] = Field(None, max_length=100)


class GanttTaskCreate(GanttTaskBase):
    pass


class GanttTaskUpdate(BaseSchema):
    task_text: Optional[str] = Field(None, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: Optional[int] = Field(None, ge=1)
    is_workday_only: Optional[bool] = None
    progress: Optional[float] = Field(None, ge=0, le=1)
    dependencies: Optional[str] = None
    assignee: Optional[str] = Field(None, max_length=100)


class GanttTaskResponse(GanttTaskBase, TimestampSchema):
    id: int
    product_id: int


# =============================================================================
# Tracker 任务 (TrackerTask) - NPI 任务
# =============================================================================

class TrackerTaskBase(BaseSchema):
    category_id: int
    stage: str = Field(default="S0", max_length=20)
    task_description: str = Field(..., max_length=500)
    function: Optional[str] = Field(None, max_length=50)
    owner: Optional[str] = Field(None, max_length=100)
    priority: str = Field(default="P2", max_length=10)
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    planned_days: Optional[int] = None
    status: str = Field(default="pending", max_length=20)
    actual_date: Optional[date] = None
    delay_days: Optional[int] = None
    risk_flag: Optional[str] = Field(None, max_length=50)
    checklist: Optional[list[dict]] = Field(default_factory=list)
    notes: Optional[str] = None


class TrackerTaskCreate(TrackerTaskBase):
    project_id: Optional[int] = None
    gantt_task_id: Optional[int] = None


class TrackerTaskUpdate(BaseSchema):
    category_id: Optional[int] = None
    stage: Optional[str] = Field(None, max_length=20)
    task_description: Optional[str] = Field(None, max_length=500)
    function: Optional[str] = Field(None, max_length=50)
    owner: Optional[str] = Field(None, max_length=100)
    priority: Optional[str] = Field(None, max_length=10)
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    planned_days: Optional[int] = None
    status: Optional[str] = Field(None, max_length=20)
    actual_date: Optional[date] = None
    delay_days: Optional[int] = None
    risk_flag: Optional[str] = Field(None, max_length=50)
    checklist: Optional[list[dict]] = None
    notes: Optional[str] = None
    gantt_task_id: Optional[int] = None


class TrackerTaskResponse(TrackerTaskBase, TimestampSchema):
    id: int
    project_id: int
    gantt_task_id: Optional[int] = None


class TrackerTaskBrief(BaseSchema):
    id: int
    category_id: int
    task_description: str
    stage: str
    status: str
    priority: str
    owner: Optional[str] = None


# =============================================================================
# 风险 (Risk)
# =============================================================================

class RiskBase(BaseSchema):
    category: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    mitigation_plan: Optional[str] = None
    risk_level: str = Field(default="Medium", max_length=20)
    risk_type: Optional[str] = Field(None, max_length=50)
    status: str = Field(default="Processing", max_length=20)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class RiskCreate(RiskBase):
    project_id: Optional[int] = None


class RiskUpdate(BaseSchema):
    category: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    mitigation_plan: Optional[str] = None
    risk_level: Optional[str] = Field(None, max_length=20)
    risk_type: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = Field(None, max_length=20)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class RiskResponse(RiskBase, TimestampSchema):
    id: int
    product_id: int
    date_alert: Optional[str] = None


class RiskBrief(BaseSchema):
    id: int
    category: Optional[str] = None
    title: str
    risk_level: str
    status: str
    date_alert: Optional[str] = None


# =============================================================================
# 变更日志 (ChangeLog)
# =============================================================================

class ChangeLogBase(BaseSchema):
    entity_type: str = Field(..., max_length=30)
    entity_id: int
    entity_name: Optional[str] = Field(None, max_length=200)
    change_type: str = Field(..., max_length=20)
    source: str = Field(default="manual", max_length=20)
    change_summary: str
    change_detail: Optional[list[dict[str, Any]]] = Field(default_factory=list)
    changed_by: Optional[str] = Field(None, max_length=100)


class ChangeLogCreate(ChangeLogBase):
    pass


class ChangeLogResponse(ChangeLogBase, TimestampSchema):
    id: int


# =============================================================================
# 聚合响应
# =============================================================================

class ProductDetailResponse(ProductResponse):
    customer: Optional[CustomerBrief] = None
    orders: list[ProductOrderBrief] = []
    bom_versions: list[BOMVersionBrief] = []
    projects: list[ProjectBrief] = []
    documents: list[DocumentBrief] = []
    risks: list[RiskBrief] = []


class BOMVersionDetailResponse(BOMVersionResponse):
    bom_items: list[BOMItemBrief] = []


class DocumentDetailResponse(DocumentResponse):
    latest_version: Optional[DocumentVersionResponse] = None
    versions: list[DocumentVersionResponse] = []


class ProjectDetailResponse(ProjectResponse):
    gantt_tasks: list[GanttTaskResponse] = []
    tracker_tasks: list[TrackerTaskBrief] = []