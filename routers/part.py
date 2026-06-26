from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import PartCreate, PartResponse

router = APIRouter(prefix="/parts", tags=["Parts"])


@router.post("/", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
def create_part(payload: PartCreate, db: Session = Depends(get_db)):
    # check unique part_code
    existing = db.query(models.Part).filter(models.Part.part_code == payload.part_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="part_code already exists")

    part = models.Part(
        part_code=payload.part_code,
        name=payload.name,
        revision=payload.revision,
        unit=payload.unit,
        category=payload.category,
        description=payload.description,
    )
    db.add(part)
    db.commit()
    db.refresh(part)
    return part


@router.get("/", response_model=List[PartResponse])
def list_parts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    parts = db.query(models.Part).offset(skip).limit(limit).all()
    return parts


@router.get("/{part_id}", response_model=PartResponse)
def get_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(models.Part).get(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


@router.put("/{part_id}", response_model=PartResponse)
def update_part(part_id: int, payload: PartCreate, db: Session = Depends(get_db)):
    part = db.query(models.Part).get(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    # if updating part_code, ensure uniqueness
    if payload.part_code != part.part_code:
        exists = db.query(models.Part).filter(models.Part.part_code == payload.part_code).first()
        if exists:
            raise HTTPException(status_code=400, detail="part_code already exists")

    part.part_code = payload.part_code
    part.name = payload.name
    part.revision = payload.revision
    part.unit = payload.unit
    part.category = payload.category
    part.description = payload.description
    db.add(part)
    db.commit()
    db.refresh(part)
    return part


@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(models.Part).get(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    db.delete(part)
    db.commit()
    return None
