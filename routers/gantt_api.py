from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models

router = APIRouter(prefix="/api", tags=["Gantt"])


@router.get("/products/{product_id}/gantt-tasks", response_model=list[dict])
def get_gantt_tasks(product_id: int, db: Session = Depends(get_db)):
    tasks = db.query(models.GanttTask).filter(
        models.GanttTask.product_id == product_id
    ).order_by(models.GanttTask.start_date.asc()).all()
    result = []
    for task in tasks:
        result.append({
            "id": task.id,
            "text": task.task_text,
            "start_date": str(task.start_date),
            "end_date": str(task.end_date),
            "duration": task.duration,
            "is_workday_only": task.is_workday_only,
            "progress": task.progress,
            "dependencies": task.dependencies,
            "assignee": task.assignee,
            "created_at": task.created_at.isoformat() if task.created_at else None
        })
    return result


@router.post("/gantt-tasks", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_gantt_task(payload: dict, db: Session = Depends(get_db)):
    product_id = payload.get("product_id")
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")
    
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    task = models.GanttTask(
        product_id=product_id,
        task_text=payload.get("text", ""),
        start_date=payload.get("start_date"),
        end_date=payload.get("end_date"),
        duration=payload.get("duration", 1),
        is_workday_only=payload.get("is_workday_only", False),
        progress=payload.get("progress", 0),
        dependencies=payload.get("dependencies", ""),
        assignee=payload.get("assignee", "")
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return {
        "id": task.id,
        "text": task.task_text,
        "start_date": str(task.start_date),
        "end_date": str(task.end_date),
        "duration": task.duration,
        "is_workday_only": task.is_workday_only,
        "progress": task.progress,
        "dependencies": task.dependencies,
        "assignee": task.assignee,
        "product_id": task.product_id,
        "created_at": task.created_at.isoformat() if task.created_at else None
    }


@router.put("/gantt-tasks/{task_id}", response_model=dict)
def update_gantt_task(task_id: int, payload: dict, db: Session = Depends(get_db)):
    task = db.query(models.GanttTask).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if "text" in payload:
        task.task_text = payload["text"]
    if "start_date" in payload:
        task.start_date = payload["start_date"]
    if "end_date" in payload:
        task.end_date = payload["end_date"]
    if "duration" in payload:
        task.duration = payload["duration"]
    if "is_workday_only" in payload:
        task.is_workday_only = payload["is_workday_only"]
    if "progress" in payload:
        task.progress = payload["progress"]
    if "dependencies" in payload:
        task.dependencies = payload["dependencies"]
    if "assignee" in payload:
        task.assignee = payload["assignee"]
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return {
        "id": task.id,
        "text": task.task_text,
        "start_date": str(task.start_date),
        "end_date": str(task.end_date),
        "duration": task.duration,
        "is_workday_only": task.is_workday_only,
        "progress": task.progress,
        "dependencies": task.dependencies,
        "assignee": task.assignee,
        "product_id": task.product_id,
        "created_at": task.created_at.isoformat() if task.created_at else None
    }


@router.delete("/gantt-tasks/{task_id}", response_model=dict)
def delete_gantt_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.GanttTask).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return {"status": "success", "message": "任务已删除"}


@router.get("/sys-holidays", response_model=list[dict])
def get_sys_holidays(db: Session = Depends(get_db)):
    holidays = db.query(models.SysHoliday).order_by(models.SysHoliday.date.asc()).all()
    return [{"holiday_date": str(h.date), "holiday_name": h.note} for h in holidays]


@router.post("/sys-holidays", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_sys_holiday(payload: dict, db: Session = Depends(get_db)):
    holiday_date = payload.get("holiday_date")
    holiday_name = payload.get("holiday_name", "")
    
    existing = db.query(models.SysHoliday).filter(
        models.SysHoliday.date == holiday_date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该日期已存在")
    
    holiday = models.SysHoliday(date=holiday_date, note=holiday_name)
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    
    return {"holiday_date": str(holiday.date), "holiday_name": holiday.note}


@router.delete("/sys-holidays/{holiday_date}", response_model=dict)
def delete_sys_holiday(holiday_date: str, db: Session = Depends(get_db)):
    holiday = db.query(models.SysHoliday).filter(
        models.SysHoliday.date == holiday_date
    ).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    db.delete(holiday)
    db.commit()
    return {"status": "success", "message": "节假日已删除"}


@router.get("/task-templates", response_model=list[dict])
def get_task_templates(db: Session = Depends(get_db)):
    templates = db.query(models.TaskTemplate).order_by(models.TaskTemplate.id.asc()).all()
    return [{"id": t.id, "template_name": t.name, "default_duration": t.default_duration} for t in templates]


@router.post("/task-templates", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_task_template(payload: dict, db: Session = Depends(get_db)):
    template_name = payload.get("template_name")
    if not template_name:
        raise HTTPException(status_code=400, detail="模板名称不能为空")
    
    template = models.TaskTemplate(
        name=template_name,
        default_duration=payload.get("default_duration", 1)
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {"id": template.id, "template_name": template.name, "default_duration": template.default_duration}


@router.delete("/task-templates/{template_id}", response_model=dict)
def delete_task_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(models.TaskTemplate).get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    return {"status": "success", "message": "模板已删除"}