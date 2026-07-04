from typing import List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import RiskCreate, RiskResponse, RiskUpdate

router = APIRouter(prefix="/products/{product_id}/risks", tags=["Risks"])


def calculate_date_alert(risk):
    if risk.status == "Done":
        return "Done"
    if risk.end_date is None:
        return None
    today = date.today()
    diff_days = (risk.end_date - today).days
    if diff_days < 0:
        return "<0 day"
    elif diff_days <= 7:
        return "<7 day"
    else:
        return ">7 day"


@router.get("", response_model=List[RiskResponse])
def get_risks(
    product_id: int,
    risk_level: str | None = None,
    status: str | None = None,
    risk_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    q = db.query(models.Risk).filter(models.Risk.product_id == product_id)
    if risk_level is not None:
        q = q.filter(models.Risk.risk_level == risk_level)
    if status is not None:
        q = q.filter(models.Risk.status == status)
    if risk_type is not None:
        q = q.filter(models.Risk.risk_type == risk_type)
    
    risks = q.offset(skip).limit(limit).all()
    
    for risk in risks:
        risk.date_alert = calculate_date_alert(risk)
    
    return risks


@router.post("", response_model=RiskResponse, status_code=status.HTTP_201_CREATED)
def create_risk(product_id: int, payload: RiskCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if payload.project_id is not None:
        project = db.query(models.Project).filter(
            models.Project.id == payload.project_id,
            models.Project.product_id == product_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    
    risk = models.Risk(
        product_id=product_id,
        project_id=payload.project_id,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        mitigation_plan=payload.mitigation_plan,
        risk_level=payload.risk_level,
        risk_type=payload.risk_type,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    risk.date_alert = calculate_date_alert(risk)
    return risk


@router.get("/{risk_id}", response_model=RiskResponse)
def get_risk(product_id: int, risk_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    risk = db.query(models.Risk).filter(
        models.Risk.id == risk_id,
        models.Risk.product_id == product_id
    ).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    risk.date_alert = calculate_date_alert(risk)
    return risk


@router.put("/{risk_id}", response_model=RiskResponse)
def update_risk(product_id: int, risk_id: int, payload: RiskUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    risk = db.query(models.Risk).filter(
        models.Risk.id == risk_id,
        models.Risk.product_id == product_id
    ).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    if payload.project_id is not None:
        project = db.query(models.Project).filter(
            models.Project.id == payload.project_id,
            models.Project.product_id == product_id
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        risk.project_id = payload.project_id
    
    if payload.category is not None:
        risk.category = payload.category
    if payload.title is not None:
        risk.title = payload.title
    if payload.description is not None:
        risk.description = payload.description
    if payload.mitigation_plan is not None:
        risk.mitigation_plan = payload.mitigation_plan
    if payload.risk_level is not None:
        risk.risk_level = payload.risk_level
    if payload.risk_type is not None:
        risk.risk_type = payload.risk_type
    if payload.status is not None:
        risk.status = payload.status
    if payload.start_date is not None:
        risk.start_date = payload.start_date
    if payload.end_date is not None:
        risk.end_date = payload.end_date
    
    db.add(risk)
    db.commit()
    db.refresh(risk)
    
    risk.date_alert = calculate_date_alert(risk)
    return risk


@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_risk(product_id: int, risk_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    risk = db.query(models.Risk).filter(
        models.Risk.id == risk_id,
        models.Risk.product_id == product_id
    ).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    db.delete(risk)
    db.commit()
    return None