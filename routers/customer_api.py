from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import CustomerCreate, CustomerResponse, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Customer).filter(models.Customer.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Customer name already exists")
    
    customer = models.Customer(
        name=payload.name,
        background=payload.background,
        team_info=payload.team_info,
        website=payload.website,
        industry=payload.industry,
        company_scale=payload.company_scale,
        location=payload.location,
        pm_contact=payload.pm_contact,
        status=payload.status,
        tier=payload.tier,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=List[CustomerResponse])
def list_customers(
    skip: int = 0,
    limit: int = 100,
    tier: str | None = None,
    status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.Customer)
    if tier is not None:
        q = q.filter(models.Customer.tier == tier)
    if status is not None:
        q = q.filter(models.Customer.status == status)
    if search is not None:
        q = q.filter(models.Customer.name.contains(search))
    customers = q.offset(skip).limit(limit).all()
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if payload.name is not None:
        existing = db.query(models.Customer).filter(
            models.Customer.name == payload.name,
            models.Customer.id != customer_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Customer name already exists")
        customer.name = payload.name
    
    if payload.background is not None:
        customer.background = payload.background
    if payload.team_info is not None:
        customer.team_info = payload.team_info
    if payload.website is not None:
        customer.website = payload.website
    if payload.industry is not None:
        customer.industry = payload.industry
    if payload.company_scale is not None:
        customer.company_scale = payload.company_scale
    if payload.location is not None:
        customer.location = payload.location
    if payload.pm_contact is not None:
        customer.pm_contact = payload.pm_contact
    if payload.status is not None:
        customer.status = payload.status
    if payload.tier is not None:
        customer.tier = payload.tier
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    active_products = db.query(models.Product).filter(
        models.Product.customer_id == customer_id,
        models.Product.status == "active"
    ).first()
    if active_products:
        raise HTTPException(status_code=400, detail="Cannot delete customer with active products")
    
    customer.status = "archived"
    db.add(customer)
    db.commit()
    return None


@router.get("/{customer_id}/products", response_model=List[dict])
def get_customer_products(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    products = db.query(models.Product).filter(
        models.Product.customer_id == customer_id
    ).all()
    
    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "status": p.status,
            "lifecycle_stage": p.lifecycle_stage,
        })
    return result