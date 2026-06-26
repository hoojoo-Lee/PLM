from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    TimelineCreate,
    TimelineResponse,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Project).filter(models.Project.project_code == payload.project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="project_code already exists")
    project = models.Project(
        project_code=payload.project_code,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/", response_model=List[ProjectResponse])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = db.query(models.Project).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.project_code = payload.project_code
    project.name = payload.name
    project.description = payload.description
    project.status = payload.status
    project.start_date = payload.start_date
    project.end_date = payload.end_date
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None


@router.get("/{project_id}/timelines", response_model=List[TimelineResponse])
def get_project_timelines(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    timelines = db.query(models.Timeline).filter(models.Timeline.project_id == project_id).all()
    return timelines
