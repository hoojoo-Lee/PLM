from datetime import date, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import TrackerTaskCreate, TrackerTaskResponse, TrackerTaskUpdate

router = APIRouter(prefix="/products/{product_id}/tracker-tasks", tags=["Tracker"])


@router.get("", response_model=List[TrackerTaskResponse])
def get_tracker_tasks(
    product_id: int,
    project_id: int | None = None,
    stage: str | None = None,
    category_id: int | None = None,
    status: str | None = None,
    owner: str | None = None,
    gantt_task_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    project_ids = [p.id for p in product.projects]
    
    q = db.query(models.TrackerTask).filter(
        models.TrackerTask.product_id == product_id,
        models.TrackerTask.project_id.in_(project_ids + [None])
    )
    
    if project_id is not None:
        q = q.filter(models.TrackerTask.project_id == project_id)
    
    if stage is not None:
        q = q.filter(models.TrackerTask.stage == stage)
    if category_id is not None:
        q = q.filter(models.TrackerTask.category_id == category_id)
    if status is not None:
        q = q.filter(models.TrackerTask.status == status)
    if owner is not None:
        q = q.filter(models.TrackerTask.owner == owner)
    if gantt_task_id is not None:
        q = q.filter(models.TrackerTask.gantt_task_id == gantt_task_id)
    
    tasks = q.offset(skip).limit(limit).all()
    return tasks


@router.post("", response_model=TrackerTaskResponse, status_code=status.HTTP_201_CREATED)
def create_tracker_task(product_id: int, payload: TrackerTaskCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    category = db.query(models.NPICategory).get(payload.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="NPI Category not found")
    
    if payload.project_id is not None:
        project = db.query(models.Project).filter(
            models.Project.id == payload.project_id,
            models.Project.product_id == product_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    if payload.gantt_task_id is not None:
        gantt_task = db.query(models.GanttTask).filter(
            models.GanttTask.id == payload.gantt_task_id,
            models.GanttTask.product_id == product_id
        ).first()
        if not gantt_task:
            raise HTTPException(status_code=404, detail="Gantt Task not found")
    
    task = models.TrackerTask(
        product_id=product_id,
        project_id=payload.project_id,
        category_id=payload.category_id,
        gantt_task_id=payload.gantt_task_id,
        stage=payload.stage,
        task_description=payload.task_description,
        function=payload.function,
        owner=payload.owner,
        priority=payload.priority,
        start_date=payload.start_date,
        deadline=payload.deadline,
        planned_days=payload.planned_days,
        status=payload.status,
        actual_date=payload.actual_date,
        delay_days=payload.delay_days,
        risk_flag=payload.risk_flag,
        checklist=payload.checklist,
        notes=payload.notes,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TrackerTaskResponse)
def get_tracker_task(product_id: int, task_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    task = db.query(models.TrackerTask).filter(
        models.TrackerTask.id == task_id,
        models.TrackerTask.product_id == product_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tracker Task not found")
    return task


@router.put("/{task_id}", response_model=TrackerTaskResponse)
def update_tracker_task(product_id: int, task_id: int, payload: TrackerTaskUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    task = db.query(models.TrackerTask).filter(
        models.TrackerTask.id == task_id,
        models.TrackerTask.product_id == product_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tracker Task not found")
    
    if payload.category_id is not None:
        category = db.query(models.NPICategory).get(payload.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="NPI Category not found")
        task.category_id = payload.category_id
    
    if payload.gantt_task_id is not None:
        if payload.gantt_task_id == 0:
            task.gantt_task_id = None
        else:
            gantt_task = db.query(models.GanttTask).filter(
                models.GanttTask.id == payload.gantt_task_id,
                models.GanttTask.product_id == product_id
            ).first()
            if not gantt_task:
                raise HTTPException(status_code=404, detail="Gantt Task not found")
            task.gantt_task_id = payload.gantt_task_id
    
    if payload.stage is not None:
        task.stage = payload.stage
    if payload.task_description is not None:
        task.task_description = payload.task_description
    if payload.function is not None:
        task.function = payload.function
    if payload.owner is not None:
        task.owner = payload.owner
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.start_date is not None:
        task.start_date = payload.start_date
    if payload.deadline is not None:
        task.deadline = payload.deadline
    if payload.planned_days is not None:
        task.planned_days = payload.planned_days
    if payload.status is not None:
        task.status = payload.status
    if payload.actual_date is not None:
        task.actual_date = payload.actual_date
    if payload.delay_days is not None:
        task.delay_days = payload.delay_days
    if payload.risk_flag is not None:
        task.risk_flag = payload.risk_flag
    if payload.checklist is not None:
        task.checklist = payload.checklist
    if payload.notes is not None:
        task.notes = payload.notes
    
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tracker_task(product_id: int, task_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    task = db.query(models.TrackerTask).filter(
        models.TrackerTask.id == task_id,
        models.TrackerTask.product_id == product_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tracker Task not found")
    
    db.delete(task)
    db.commit()
    return None


@router.post("/init-stage", response_model=List[TrackerTaskResponse])
def init_stage_tasks(product_id: int, payload: dict, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    stage = payload.get("stage")
    project_id = payload.get("project_id")
    
    if not stage:
        raise HTTPException(status_code=400, detail="stage is required")
    
    if project_id is not None:
        project = db.query(models.Project).filter(
            models.Project.id == project_id,
            models.Project.product_id == product_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    categories = db.query(models.NPICategory).filter(
        models.NPICategory.applicable_stages.contains(stage)
    ).all()
    
    created_tasks = []
    for category in categories:
        existing = db.query(models.TrackerTask).filter(
            models.TrackerTask.product_id == product_id,
            models.TrackerTask.category_id == category.id,
            models.TrackerTask.stage == stage,
            models.TrackerTask.project_id == project_id
        ).first()
        if existing:
            continue
        
        task = models.TrackerTask(
            product_id=product_id,
            project_id=project_id,
            category_id=category.id,
            stage=stage,
            task_description=category.typical_task or f"{category.name} - {stage} 任务",
            function="",
            owner="",
            priority="P2",
            status="pending",
        )
        db.add(task)
        created_tasks.append(task)
    
    db.commit()
    for task in created_tasks:
        db.refresh(task)
    
    return created_tasks


@router.post("/{task_id}/sync-to-gantt", response_model=dict)
def sync_tracker_to_gantt(product_id: int, task_id: int, payload: dict, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    tracker_task = db.query(models.TrackerTask).filter(
        models.TrackerTask.id == task_id,
        models.TrackerTask.product_id == product_id
    ).first()
    if not tracker_task:
        raise HTTPException(status_code=404, detail="Tracker Task not found")
    
    if tracker_task.gantt_task_id:
        raise HTTPException(status_code=400, detail="Task already synced to gantt")
    
    start_date = payload.get('start_date')
    duration = payload.get('duration', 1)
    assignee = payload.get('assignee', '')
    
    if start_date:
        start_date_obj = date.fromisoformat(start_date)
        end_date_obj = start_date_obj + timedelta(days=duration - 1)
    else:
        start_date_obj = date.today()
        end_date_obj = start_date_obj + timedelta(days=duration - 1)
    
    gantt_task = models.GanttTask(
        product_id=product_id,
        task_text=tracker_task.task_description,
        start_date=start_date_obj,
        end_date=end_date_obj,
        duration=duration,
        assignee=assignee,
        progress=0.0,
        is_workday_only=True,
    )
    db.add(gantt_task)
    db.commit()
    db.refresh(gantt_task)
    
    tracker_task.gantt_task_id = gantt_task.id
    db.add(tracker_task)
    db.commit()
    
    return {"status": "success", "gantt_task_id": gantt_task.id}