from typing import List
from datetime import date
import json
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import DocumentCreate, DocumentResponse, DocumentUpdate

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(payload: DocumentCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.bom_item_id is not None:
        bom_item = db.query(models.BOMItem).get(payload.bom_item_id)
        if not bom_item:
            raise HTTPException(status_code=404, detail="BOMItem not found")
    effective_received_date = payload.received_date if payload.received_date else date.today()
    effective_version = payload.version if payload.version else "1"
    effective_drive_id = extract_drive_id(payload.google_drive_id)
    document = models.Document(
        product_id=payload.product_id,
        bom_item_id=payload.bom_item_id,
        title=payload.title,
        document_type=payload.document_type,
        version=effective_version,
        received_date=effective_received_date,
        google_drive_id=effective_drive_id,
        file_name=payload.file_name,
        file_size=payload.file_size,
        mime_type=payload.mime_type,
        status=payload.status,
        update_notes=payload.update_notes,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    product_id: int | None = None,
    bom_item_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    q = db.query(models.Document)
    if product_id is not None:
        q = q.filter(models.Document.product_id == product_id)
    if bom_item_id is not None:
        q = q.filter(models.Document.bom_item_id == bom_item_id)
    documents = q.offset(skip).limit(limit).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(models.Document).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(document_id: int, payload: DocumentUpdate, db: Session = Depends(get_db)):
    document = db.query(models.Document).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    old_version = document.version
    old_drive_id = document.google_drive_id
    need_version_bump = False
    drive_id_changed = False
    new_drive_id = old_drive_id
    
    if payload.product_id is not None:
        product = db.query(models.Product).get(payload.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        document.product_id = payload.product_id
    if payload.bom_item_id is not None:
        bom_item = db.query(models.BOMItem).get(payload.bom_item_id)
        if not bom_item:
            raise HTTPException(status_code=404, detail="BOMItem not found")
        document.bom_item_id = payload.bom_item_id
    if payload.title is not None:
        document.title = payload.title
    if payload.document_type is not None:
        document.document_type = payload.document_type
    if payload.received_date is not None:
        document.received_date = payload.received_date
    if payload.version is not None:
        document.version = payload.version
    if payload.google_drive_id is not None:
        effective_drive_id = extract_drive_id(payload.google_drive_id)
        new_drive_id = effective_drive_id
        if effective_drive_id != old_drive_id:
            drive_id_changed = True
            if not payload.version:
                need_version_bump = True
        document.google_drive_id = effective_drive_id
    if payload.file_name is not None:
        document.file_name = payload.file_name
    if payload.file_size is not None:
        document.file_size = payload.file_size
    if payload.mime_type is not None:
        document.mime_type = payload.mime_type
    if payload.status is not None:
        document.status = payload.status
    if payload.update_notes is not None:
        document.update_notes = payload.update_notes
    
    if need_version_bump:
        new_version = bump_version(old_version)
        document.version = new_version
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    change_summary = f"文档更新"
    if need_version_bump:
        change_summary = f"文档版本升级: V{old_version} -> V{document.version}"
    elif drive_id_changed:
        change_summary = f"文档文件替换: V{document.version}"
    
    change_detail = {
        "old_version": old_version,
        "new_version": document.version,
        "drive_id_changed": drive_id_changed,
        "old_drive_id": old_drive_id,
        "new_drive_id": new_drive_id,
        "update_notes": payload.update_notes or document.update_notes or ""
    }
    
    changelog = models.ChangeLog(
        entity_type="Doc",
        entity_id=document.id,
        entity_name=document.title,
        change_type="update",
        change_summary=change_summary,
        change_detail=json.dumps(change_detail),
    )
    db.add(changelog)
    db.commit()
    
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(models.Document).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_title = document.title
    doc_drive_id = document.google_drive_id
    
    changelog = models.ChangeLog(
        entity_type="Doc",
        entity_id=document.id,
        entity_name=doc_title,
        change_type="delete",
        change_summary=f"删除文档: {doc_title}",
        change_detail=json.dumps({"action": "delete_document", "document_title": doc_title, "google_drive_id": doc_drive_id}),
    )
    db.add(changelog)
    db.delete(document)
    db.commit()
    return None


@router.get("/bom-items/{bom_item_id}/documents", response_model=List[DocumentResponse])
def get_bom_item_documents(bom_item_id: int, db: Session = Depends(get_db)):
    bom_item = db.query(models.BOMItem).get(bom_item_id)
    if not bom_item:
        raise HTTPException(status_code=404, detail="BOMItem not found")
    documents = db.query(models.Document).filter(models.Document.bom_item_id == bom_item_id).all()
    return documents


def bump_version(old_version: str) -> str:
    match = re.search(r'(\d+)$', old_version)
    if match:
        num = int(match.group(1))
        return old_version[:match.start()] + str(num + 1)
    match = re.search(r'(\d+\.\d+)$', old_version)
    if match:
        parts = match.group(1).split('.')
        if len(parts) == 2:
            return old_version[:match.start()] + f"{parts[0]}.{int(parts[1]) + 1}"
    try:
        return str(int(old_version) + 1)
    except ValueError:
        return old_version + "_v2"


def extract_drive_id(input_str: str) -> str:
    if not input_str:
        return ''
    trimmed = input_str.strip()
    file_d_regex = re.compile(r'/file/d/([-\w]+)')
    open_id_regex = re.compile(r'/open\?id=([-\w]+)')
    query_id_regex = re.compile(r'[?&]id=([-\w]+)')
    match = file_d_regex.search(trimmed) or open_id_regex.search(trimmed) or query_id_regex.search(trimmed)
    if match:
        return match.group(1)
    long_match = re.search(r'[-\w]{25,}', trimmed)
    if long_match:
        return long_match.group(0)
    return trimmed
