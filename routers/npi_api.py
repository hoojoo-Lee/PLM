from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import NPICategoryResponse, SysHolidayCreate, SysHolidayResponse, TaskTemplateCreate, TaskTemplateResponse

router = APIRouter(prefix="/api", tags=["NPI"])


@router.get("/npi-categories", response_model=List[NPICategoryResponse])
def get_npi_categories(db: Session = Depends(get_db)):
    categories = db.query(models.NPICategory).order_by(models.NPICategory.id.asc()).all()
    return categories


@router.get("/npi-categories/{category_id}", response_model=NPICategoryResponse)
def get_npi_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(models.NPICategory).get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="NPI Category not found")
    return category


@router.get("/sys-holidays", response_model=List[SysHolidayResponse])
def get_sys_holidays(db: Session = Depends(get_db)):
    holidays = db.query(models.SysHoliday).order_by(models.SysHoliday.date.asc()).all()
    return holidays


@router.post("/sys-holidays", response_model=SysHolidayResponse, status_code=status.HTTP_201_CREATED)
def create_sys_holiday(payload: SysHolidayCreate, db: Session = Depends(get_db)):
    existing = db.query(models.SysHoliday).filter(
        models.SysHoliday.date == payload.date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Holiday date already exists")
    
    holiday = models.SysHoliday(date=payload.date, note=payload.note)
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


@router.delete("/sys-holidays/{holiday_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sys_holiday(holiday_date: str, db: Session = Depends(get_db)):
    from datetime import date as date_type
    try:
        holiday_date_obj = date_type.fromisoformat(holiday_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    holiday = db.query(models.SysHoliday).filter(
        models.SysHoliday.date == holiday_date_obj
    ).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    db.delete(holiday)
    db.commit()
    return None


@router.get("/task-templates", response_model=List[TaskTemplateResponse])
def get_task_templates(db: Session = Depends(get_db)):
    templates = db.query(models.TaskTemplate).order_by(models.TaskTemplate.id.asc()).all()
    return templates


@router.post("/task-templates", response_model=TaskTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_task_template(payload: TaskTemplateCreate, db: Session = Depends(get_db)):
    template = models.TaskTemplate(
        name=payload.name,
        default_duration=payload.default_duration,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/task-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(models.TaskTemplate).get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Task template not found")
    
    db.delete(template)
    db.commit()
    return None