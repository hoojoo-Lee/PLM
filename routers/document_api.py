from typing import List

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
    document = models.Document(
        product_id=payload.product_id,
        bom_item_id=payload.bom_item_id,
        title=payload.title,
        document_type=payload.document_type,
        version=payload.version,
        google_drive_id=payload.google_drive_id,
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
    if payload.version is not None:
        document.version = payload.version
    if payload.google_drive_id is not None:
        document.google_drive_id = payload.google_drive_id
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
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(models.Document).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
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
