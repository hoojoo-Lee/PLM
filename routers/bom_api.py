from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import (
    BOMItemBrief,
    BOMItemCreate,
    BOMItemResponse,
    BOMItemUpdate,
    BOMVersionCreate,
    BOMVersionDetailResponse,
    BOMVersionResponse,
    BOMVersionUpdate,
)

router = APIRouter(prefix="/bom", tags=["BOM"])


# =============================================================================
# BOM 版本 API
# =============================================================================

@router.post("/versions/", response_model=BOMVersionResponse, status_code=status.HTTP_201_CREATED)
def create_bom_version(payload: BOMVersionCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    active_version = db.query(models.BOMVersion).filter(
        models.BOMVersion.product_id == payload.product_id,
        models.BOMVersion.status == "active"
    ).first()
    if active_version:
        active_version.status = "archived"
    
    bom_version = models.BOMVersion(
        product_id=payload.product_id,
        version_code=payload.version_code,
        status=payload.status,
        received_at=payload.received_at,
        change_notes=payload.change_notes,
        created_by=payload.created_by,
    )
    db.add(bom_version)
    db.commit()
    db.refresh(bom_version)
    return bom_version


@router.get("/versions/", response_model=List[BOMVersionResponse])
def list_bom_versions(product_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(models.BOMVersion)
    if product_id is not None:
        q = q.filter(models.BOMVersion.product_id == product_id)
    versions = q.offset(skip).limit(limit).all()
    return versions


@router.get("/versions/{version_id}", response_model=BOMVersionDetailResponse)
def get_bom_version(version_id: int, db: Session = Depends(get_db)):
    version = db.query(models.BOMVersion).get(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    return version


@router.put("/versions/{version_id}", response_model=BOMVersionResponse)
def update_bom_version(version_id: int, payload: BOMVersionUpdate, db: Session = Depends(get_db)):
    version = db.query(models.BOMVersion).get(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    if payload.product_id is not None:
        product = db.query(models.Product).get(payload.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        version.product_id = payload.product_id
    if payload.version_code is not None:
        version.version_code = payload.version_code
    if payload.status is not None:
        version.status = payload.status
    if payload.received_at is not None:
        version.received_at = payload.received_at
    if payload.change_notes is not None:
        version.change_notes = payload.change_notes
    if payload.created_by is not None:
        version.created_by = payload.created_by
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.delete("/versions/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bom_version(version_id: int, db: Session = Depends(get_db)):
    version = db.query(models.BOMVersion).get(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    db.delete(version)
    db.commit()
    return None


@router.patch("/versions/{version_id}/archive", response_model=BOMVersionResponse)
def archive_bom_version(version_id: int, db: Session = Depends(get_db)):
    version = db.query(models.BOMVersion).get(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    if version.status == "archived":
        raise HTTPException(status_code=400, detail="BOMVersion is already archived")
    version.status = "archived"
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.patch("/versions/{version_id}/activate", response_model=BOMVersionResponse)
def activate_bom_version(version_id: int, db: Session = Depends(get_db)):
    version = db.query(models.BOMVersion).get(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    if version.status == "active":
        raise HTTPException(status_code=400, detail="BOMVersion is already active")
    
    active_version = db.query(models.BOMVersion).filter(
        models.BOMVersion.product_id == version.product_id,
        models.BOMVersion.status == "active"
    ).first()
    if active_version:
        active_version.status = "archived"
    
    version.status = "active"
    db.add(version)
    db.add(active_version) if active_version else None
    db.commit()
    db.refresh(version)
    return version


# =============================================================================
# BOM 物料项 API
# =============================================================================

@router.post("/items/", response_model=BOMItemResponse, status_code=status.HTTP_201_CREATED)
def create_bom_item(payload: BOMItemCreate, db: Session = Depends(get_db)):
    bom_version = db.query(models.BOMVersion).get(payload.bom_version_id)
    if not bom_version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    bom_item = models.BOMItem(
        bom_version_id=payload.bom_version_id,
        category=payload.category,
        mpn=payload.mpn,
        name=payload.name,
        quantity=payload.quantity,
        designator=payload.designator,
        responsible=payload.responsible,
        status=payload.status,
        picture_drive_id=payload.picture_drive_id,
    )
    db.add(bom_item)
    db.commit()
    db.refresh(bom_item)
    return bom_item


@router.get("/items/", response_model=List[BOMItemResponse])
def list_bom_items(bom_version_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(models.BOMItem)
    if bom_version_id is not None:
        q = q.filter(models.BOMItem.bom_version_id == bom_version_id)
    items = q.offset(skip).limit(limit).all()
    return items


@router.get("/items/{item_id}", response_model=BOMItemResponse)
def get_bom_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.BOMItem).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="BOMItem not found")
    return item


@router.put("/items/{item_id}", response_model=BOMItemResponse)
def update_bom_item(item_id: int, payload: BOMItemUpdate, db: Session = Depends(get_db)):
    item = db.query(models.BOMItem).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="BOMItem not found")
    if payload.bom_version_id is not None:
        bom_version = db.query(models.BOMVersion).get(payload.bom_version_id)
        if not bom_version:
            raise HTTPException(status_code=404, detail="BOMVersion not found")
        item.bom_version_id = payload.bom_version_id
    if payload.category is not None:
        item.category = payload.category
    if payload.mpn is not None:
        item.mpn = payload.mpn
    if payload.name is not None:
        item.name = payload.name
    if payload.quantity is not None:
        item.quantity = payload.quantity
    if payload.designator is not None:
        item.designator = payload.designator
    if payload.responsible is not None:
        item.responsible = payload.responsible
    if payload.status is not None:
        item.status = payload.status
    if payload.picture_drive_id is not None:
        item.picture_drive_id = payload.picture_drive_id
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bom_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.BOMItem).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="BOMItem not found")
    db.delete(item)
    db.commit()
    return None


@router.post("/items/batch", response_model=List[BOMItemResponse], status_code=status.HTTP_201_CREATED)
def create_bom_items_batch(bom_version_id: int, items: List[BOMItemCreate], db: Session = Depends(get_db)):
    bom_version = db.query(models.BOMVersion).get(bom_version_id)
    if not bom_version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    
    created_items = []
    for payload in items:
        payload.bom_version_id = bom_version_id
        bom_item = models.BOMItem(
            bom_version_id=payload.bom_version_id,
            category=payload.category,
            mpn=payload.mpn,
            name=payload.name,
            quantity=payload.quantity,
            designator=payload.designator,
            responsible=payload.responsible,
            status=payload.status,
            picture_drive_id=payload.picture_drive_id,
        )
        db.add(bom_item)
        created_items.append(bom_item)
    
    db.commit()
    for item in created_items:
        db.refresh(item)
    
    return created_items
