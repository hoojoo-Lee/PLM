from typing import List
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import DocumentCreate, DocumentDetailResponse, DocumentResponse, DocumentUpdate, DocumentVersionCreate, DocumentVersionResponse

router = APIRouter(prefix="/products/{product_id}/documents", tags=["Documents"])


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


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document(product_id: int, payload: DocumentCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if payload.bom_item_id is not None:
        bom_item = db.query(models.BOMItem).get(payload.bom_item_id)
        if not bom_item:
            raise HTTPException(status_code=404, detail="BOMItem not found")
    
    document = models.Document(
        product_id=product_id,
        project_id=payload.project_id,
        bom_item_id=payload.bom_item_id,
        title=payload.title,
        document_type=payload.document_type,
        category=payload.category,
        status=payload.status,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=List[DocumentDetailResponse])
def list_documents(
    product_id: int,
    document_type: str | None = None,
    category: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    q = db.query(models.Document).filter(models.Document.product_id == product_id)
    if document_type is not None:
        q = q.filter(models.Document.document_type == document_type)
    if category is not None:
        q = q.filter(models.Document.category == category)
    if status is not None:
        q = q.filter(models.Document.status == status)
    documents = q.offset(skip).limit(limit).all()
    
    result = []
    for doc in documents:
        versions = db.query(models.DocumentVersion).filter(
            models.DocumentVersion.document_id == doc.id
        ).order_by(models.DocumentVersion.created_at.desc()).all()
        
        doc_dict = DocumentResponse.model_validate(doc).model_dump()
        
        version_dicts = [DocumentVersionResponse.model_validate(v).model_dump() for v in versions]
        
        if versions:
            latest = versions[0]
            doc_dict["latest_version"] = DocumentVersionResponse.model_validate(latest).model_dump()
        
        doc_dict["versions"] = version_dicts
        result.append(doc_dict)
    
    return result


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(product_id: int, document_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.product_id == product_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    latest_version = db.query(models.DocumentVersion).filter(
        models.DocumentVersion.document_id == document_id
    ).order_by(models.DocumentVersion.created_at.desc()).first()
    
    document.latest_version = latest_version
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(product_id: int, document_id: int, payload: DocumentUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.product_id == product_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if payload.title is not None:
        document.title = payload.title
    if payload.document_type is not None:
        document.document_type = payload.document_type
    if payload.category is not None:
        document.category = payload.category
    if payload.status is not None:
        document.status = payload.status
    
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(product_id: int, document_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.product_id == product_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(document)
    db.commit()
    return None


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
def get_document_versions(product_id: int, document_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.product_id == product_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    versions = db.query(models.DocumentVersion).filter(
        models.DocumentVersion.document_id == document_id
    ).order_by(models.DocumentVersion.created_at.desc()).all()
    return versions


@router.post("/{document_id}/versions", response_model=DocumentVersionResponse, status_code=status.HTTP_201_CREATED)
def create_document_version(product_id: int, document_id: int, payload: DocumentVersionCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.product_id == product_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    latest_version = db.query(models.DocumentVersion).filter(
        models.DocumentVersion.document_id == document_id
    ).order_by(models.DocumentVersion.created_at.desc()).first()
    
    suggested_version = "1"
    if latest_version:
        suggested_version = bump_version(latest_version.version_number)
    
    effective_version = payload.version_number or suggested_version
    
    document_version = models.DocumentVersion(
        document_id=document_id,
        version_number=effective_version,
        received_date=payload.received_date,
        google_drive_id=extract_drive_id(payload.google_drive_id) if payload.google_drive_id else None,
        file_name=payload.file_name,
        file_size=payload.file_size,
        mime_type=payload.mime_type,
        responsible=payload.responsible,
        status=payload.status,
        update_notes=payload.update_notes,
    )
    db.add(document_version)
    db.commit()
    db.refresh(document_version)
    return document_version


@router.get("/{document_id}/versions/{version_id}", response_model=DocumentVersionResponse)
def get_document_version(product_id: int, document_id: int, version_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.product_id == product_id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    version = db.query(models.DocumentVersion).filter(
        models.DocumentVersion.id == version_id,
        models.DocumentVersion.document_id == document_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="DocumentVersion not found")
    return version


@router.get("/bom-items/{bom_item_id}/documents", response_model=List[DocumentResponse])
def get_bom_item_documents(product_id: int, bom_item_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    documents = db.query(models.Document).filter(
        models.Document.bom_item_id == bom_item_id,
        models.Document.product_id == product_id
    ).all()
    return documents