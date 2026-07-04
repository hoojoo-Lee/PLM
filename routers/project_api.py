from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import ProjectCreate, ProjectDetailResponse, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/products/{product_id}/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(product_id: int, payload: ProjectCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    existing = db.query(models.Project).filter(models.Project.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project code already exists")
    
    project = models.Project(
        product_id=product_id,
        customer_id=payload.customer_id,
        name=payload.name,
        code=payload.code,
        sales=payload.sales,
        pm=payload.pm,
        ee=payload.ee,
        me=payload.me,
        current_stage=payload.current_stage,
        goal=payload.goal,
        control_book_link=payload.control_book_link,
        status=payload.status,
        start_date=payload.start_date,
        target_mp_date=payload.target_mp_date,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    product_id: int,
    status: str | None = None,
    current_stage: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    q = db.query(models.Project).filter(models.Project.product_id == product_id)
    if status is not None:
        q = q.filter(models.Project.status == status)
    if current_stage is not None:
        q = q.filter(models.Project.current_stage == current_stage)
    projects = q.offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(product_id: int, project_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.product_id == product_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(product_id: int, project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.product_id == product_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if payload.code is not None:
        existing = db.query(models.Project).filter(
            models.Project.code == payload.code,
            models.Project.id != project_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Project code already exists")
        project.code = payload.code
    
    if payload.name is not None:
        project.name = payload.name
    if payload.sales is not None:
        project.sales = payload.sales
    if payload.pm is not None:
        project.pm = payload.pm
    if payload.ee is not None:
        project.ee = payload.ee
    if payload.me is not None:
        project.me = payload.me
    if payload.current_stage is not None:
        project.current_stage = payload.current_stage
    if payload.goal is not None:
        project.goal = payload.goal
    if payload.control_book_link is not None:
        project.control_book_link = payload.control_book_link
    if payload.status is not None:
        project.status = payload.status
    if payload.start_date is not None:
        project.start_date = payload.start_date
    if payload.target_mp_date is not None:
        project.target_mp_date = payload.target_mp_date
    
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(product_id: int, project_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.product_id == product_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return None


@router.get("/{project_id}/changelog", response_model=List[dict])
def get_project_changelog(product_id: int, project_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.product_id == product_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    changelogs = db.query(models.ChangeLog).filter(
        models.ChangeLog.entity_type == "Project",
        models.ChangeLog.entity_id == project_id
    ).order_by(models.ChangeLog.created_at.desc()).limit(100).all()
    return changelogs