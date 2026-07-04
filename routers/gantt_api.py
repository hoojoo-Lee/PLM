from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import GanttTaskCreate, GanttTaskResponse, GanttTaskUpdate

router = APIRouter(prefix="/products/{product_id}/gantt-tasks", tags=["Gantt"])


@router.get("", response_model=List[GanttTaskResponse])
def get_gantt_tasks(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    tasks = db.query(models.GanttTask).filter(
        models.GanttTask.product_id == product_id
    ).order_by(models.GanttTask.start_date.asc()).all()
    return tasks


@router.post("", response_model=GanttTaskResponse, status_code=status.HTTP_201_CREATED)
def create_gantt_task(product_id: int, payload: GanttTaskCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    task = models.GanttTask(
        product_id=product_id,
        task_text=payload.task_text,
        start_date=payload.start_date,
        end_date=payload.end_date,
        duration=payload.duration,
        is_workday_only=payload.is_workday_only,
        progress=payload.progress,
        dependencies=payload.dependencies,
        assignee=payload.assignee,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=GanttTaskResponse)
def update_gantt_task(product_id: int, task_id: int, payload: GanttTaskUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    task = db.query(models.GanttTask).filter(
        models.GanttTask.id == task_id,
        models.GanttTask.product_id == product_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    old_progress = task.progress
    old_status = None
    
    if payload.task_text is not None:
        task.task_text = payload.task_text
    if payload.start_date is not None:
        task.start_date = payload.start_date
    if payload.end_date is not None:
        task.end_date = payload.end_date
    if payload.duration is not None:
        task.duration = payload.duration
    if payload.is_workday_only is not None:
        task.is_workday_only = payload.is_workday_only
    if payload.progress is not None:
        task.progress = payload.progress
    if payload.dependencies is not None:
        task.dependencies = payload.dependencies
    if payload.assignee is not None:
        task.assignee = payload.assignee
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    if old_progress < 1.0 and task.progress >= 1.0:
        tracker_tasks = db.query(models.TrackerTask).filter(
            models.TrackerTask.gantt_task_id == task_id,
            models.TrackerTask.status.in_(["pending", "in_progress"])
        ).all()
        for tracker in tracker_tasks:
            tracker.status = "done"
            if tracker.actual_date is None:
                tracker.actual_date = datetime.now().date()
        db.commit()
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gantt_task(product_id: int, task_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    task = db.query(models.GanttTask).filter(
        models.GanttTask.id == task_id,
        models.GanttTask.product_id == product_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    tracker_tasks = db.query(models.TrackerTask).filter(
        models.TrackerTask.gantt_task_id == task_id
    ).all()
    for tracker in tracker_tasks:
        tracker.gantt_task_id = None
    
    db.delete(task)
    db.commit()
    return None


@router.post("/recalculate", response_model=dict)
def recalculate_gantt_tasks(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    tasks = db.query(models.GanttTask).filter(
        models.GanttTask.product_id == product_id
    ).order_by(models.GanttTask.start_date.asc()).all()
    
    holidays = {h.date for h in db.query(models.SysHoliday).all()}
    
    from datetime import timedelta
    
    def is_workday(dt):
        if dt.weekday() >= 5:
            return False
        if dt in holidays:
            return False
        return True
    
    def add_workdays(start_date, days):
        current = start_date
        added = 0
        while added < days:
            current += timedelta(days=1)
            if is_workday(current):
                added += 1
        return current
    
    for task in tasks:
        if task.is_workday_only:
            task.end_date = add_workdays(task.start_date, task.duration - 1)
        db.add(task)
    
    db.commit()
    
    return {"status": "success", "message": "甘特图任务日期已重新计算"}