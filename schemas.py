from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel


# Project schemas
class ProjectBase(BaseModel):
    project_code: str
    name: str
    description: Optional[str] = None
    status: Optional[str] = "active"
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Part schemas
class PartBase(BaseModel):
    project_id: Optional[int] = None
    part_code: str
    name: str
    revision: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    picture_drive_id: Optional[str] = None
    status: Optional[str] = "draft"
    description: Optional[str] = None


class PartCreate(PartBase):
    pass


class PartUpdate(BaseModel):
    part_code: Optional[str] = None
    name: Optional[str] = None
    revision: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    picture_drive_id: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None


class PartResponse(PartBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Timeline schemas
class TimelineBase(BaseModel):
    project_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = "pending"


class TimelineCreate(TimelineBase):
    pass


class TimelineUpdate(TimelineBase):
    pass


class TimelineResponse(TimelineBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# Document schemas
class DocumentBase(BaseModel):
    project_id: Optional[int] = None
    part_id: Optional[int] = None
    document_type: Optional[str] = None
    title: str
    google_drive_file_id: str
    version: Optional[str] = "1"
    update_notes: Optional[str] = None
    file_name: Optional[str] = None
    status: Optional[str] = "draft"


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PartBase(BaseModel):
    part_code: str
    name: str
    revision: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None


class PartCreate(PartBase):
    pass


class PartResponse(PartBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
