from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import (
    ProductCreate,
    ProductDetailResponse,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    if payload.code:
        existing = db.query(models.Product).filter(models.Product.code == payload.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product code already exists")
    product = models.Product(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        usage_scenario=payload.usage_scenario,
        key_ic_info=payload.key_ic_info,
        lifecycle_stage=payload.lifecycle_stage,
        lifecycle_history=payload.lifecycle_history,
        core_concern=payload.core_concern,
        annual_workload=payload.annual_workload,
        status=payload.status,
        customer_id=payload.customer_id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 100,
    customer_id: int | None = None,
    lifecycle_stage: str | None = None,
    status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.Product)
    if customer_id is not None:
        q = q.filter(models.Product.customer_id == customer_id)
    if lifecycle_stage is not None:
        q = q.filter(models.Product.lifecycle_stage == lifecycle_stage)
    if status is not None:
        q = q.filter(models.Product.status == status)
    if search is not None:
        q = q.filter(
            models.Product.name.contains(search) |
            models.Product.code.contains(search)
        )
    products = q.offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.code is not None:
        existing = db.query(models.Product).filter(
            models.Product.code == payload.code,
            models.Product.id != product_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product code already exists")
        product.code = payload.code
    if payload.name is not None:
        product.name = payload.name
    if payload.description is not None:
        product.description = payload.description
    if payload.usage_scenario is not None:
        product.usage_scenario = payload.usage_scenario
    if payload.key_ic_info is not None:
        product.key_ic_info = payload.key_ic_info
    if payload.lifecycle_stage is not None:
        product.lifecycle_stage = payload.lifecycle_stage
    if payload.lifecycle_history is not None:
        product.lifecycle_history = payload.lifecycle_history
    if payload.core_concern is not None:
        product.core_concern = payload.core_concern
    if payload.annual_workload is not None:
        product.annual_workload = payload.annual_workload
    if payload.status is not None:
        product.status = payload.status
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return None


@router.put("/{product_id}/lifecycle", response_model=ProductResponse)
def update_product_lifecycle(product_id: int, payload: dict, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    new_stage = payload.get("stage")
    remark = payload.get("remark", "")
    
    if not new_stage:
        raise HTTPException(status_code=400, detail="stage is required")
    
    history_entry = {
        "from": product.lifecycle_stage,
        "to": new_stage,
        "date": datetime.utcnow().isoformat(),
        "remark": remark
    }
    
    if product.lifecycle_history is None:
        product.lifecycle_history = []
    product.lifecycle_history.append(history_entry)
    product.lifecycle_stage = new_stage
    
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}/changelog", response_model=List[dict])
def get_product_changelog(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    changelogs = db.query(models.ChangeLog).filter(
        models.ChangeLog.entity_type == "Product",
        models.ChangeLog.entity_id == product_id
    ).order_by(models.ChangeLog.created_at.desc()).limit(100).all()
    return changelogs