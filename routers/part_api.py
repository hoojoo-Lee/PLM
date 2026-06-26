from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
import models
from schemas import PartCreate, PartResponse, PartUpdate

router = APIRouter(prefix="/parts", tags=["Parts"])


def write_changelog(db: Session, project_id: int | None, entity_type: str, entity_key: str | None, change_type: str, diff: dict, changed_by: str | None = None):
    entry = models.ChangeLog(
        project_id=project_id,
        entity_type=entity_type,
        entity_key=entity_key,
        change_type=change_type,
        diff=diff,
        changed_by=changed_by,
    )
    db.add(entry)
    db.commit()


@router.post("/", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
def create_part(payload: PartCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Part).filter(models.Part.part_code == payload.part_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="part_code already exists")

    part = models.Part(
        project_id=payload.project_id,
        part_code=payload.part_code,
        name=payload.name,
        revision=payload.revision,
        category=payload.category,
        unit=payload.unit,
        picture_drive_id=payload.picture_drive_id,
        status=payload.status,
        description=payload.description,
    )
    db.add(part)
    db.commit()
    db.refresh(part)

    # write changelog
    write_changelog(db, part.project_id, "Part", part.part_code, "create", {"id": part.id, "part_code": part.part_code})

    return part


@router.get("/", response_model=List[PartResponse])
def list_parts(project_id: int | None = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(models.Part)
    if project_id is not None:
        q = q.filter(models.Part.project_id == project_id)
    parts = q.offset(skip).limit(limit).all()
    return parts


@router.get("/{part_id}", response_model=PartResponse)
def get_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(models.Part).get(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part


@router.put("/{part_id}", response_model=PartResponse)
def update_part(part_id: int, payload: PartUpdate, db: Session = Depends(get_db)):
    part = db.query(models.Part).get(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")

    before = {"id": part.id, "status": part.status}

    if payload.part_code is not None:
        # check uniqueness
        exists = db.query(models.Part).filter(models.Part.part_code == payload.part_code, models.Part.id != part_id).first()
        if exists:
            raise HTTPException(status_code=400, detail="part_code already exists")
        part.part_code = payload.part_code
    if payload.name is not None:
        part.name = payload.name
    if payload.revision is not None:
        part.revision = payload.revision
    if payload.category is not None:
        part.category = payload.category
    if payload.unit is not None:
        part.unit = payload.unit
    if payload.picture_drive_id is not None:
        part.picture_drive_id = payload.picture_drive_id
    if payload.status is not None:
        part.status = payload.status
    if payload.description is not None:
        part.description = payload.description

    db.add(part)
    db.commit()
    db.refresh(part)

    after = {"id": part.id, "status": part.status}
    diff = {"before": before, "after": after}

    # write changelog
    write_changelog(db, part.project_id, "Part", part.part_code, "update", diff)

    return part


@router.delete("/{part_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_part(part_id: int, db: Session = Depends(get_db)):
    part = db.query(models.Part).get(part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    db.delete(part)
    db.commit()
    return None
