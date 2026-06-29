from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import (
    BOMVersionBrief,
    BOMVersionCreate,
    BOMVersionResponse,
    DocumentResponse,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProjectBrief,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Product).filter(models.Product.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product code already exists")
    product = models.Product(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        status=payload.status,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/", response_model=List[ProductResponse])
def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=ProductResponse)
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


@router.get("/{product_id}/projects", response_model=List[ProjectBrief])
def get_product_projects(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    projects = db.query(models.Project).filter(models.Project.product_id == product_id).all()
    return projects


@router.get("/{product_id}/bom-versions", response_model=List[BOMVersionBrief])
def get_product_bom_versions(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    versions = db.query(models.BOMVersion).filter(models.BOMVersion.product_id == product_id).all()
    return versions


@router.post("/{product_id}/bom-versions", response_model=BOMVersionResponse, status_code=status.HTTP_201_CREATED)
def create_bom_version(product_id: int, payload: BOMVersionCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    existing = db.query(models.BOMVersion).filter(
        models.BOMVersion.product_id == product_id,
        models.BOMVersion.version_code == payload.version_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Version code already exists for this product")
    bom_version = models.BOMVersion(
        product_id=product_id,
        version_code=payload.version_code,
        status="active",
        change_notes=payload.change_notes,
    )
    db.add(bom_version)
    db.commit()
    db.refresh(bom_version)
    return bom_version


@router.get("/{product_id}/documents", response_model=List[DocumentResponse])
def get_product_global_documents(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    documents = db.query(models.Document).filter(
        models.Document.product_id == product_id,
        models.Document.bom_item_id.is_(None)
    ).all()
    return documents
