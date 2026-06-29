from typing import List
from datetime import date
import json
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
from schemas import ChangeLogResponse, DocumentCreate, DocumentResponse, DocumentUpdate

router = APIRouter(prefix="/documents", tags=["Documents"])

ENTITY_TYPE_DOCUMENT = "Doc"


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
    
    # 兜底处理：确保 version 字段不为空
    for doc in documents:
        if not doc.version or not str(doc.version).strip():
            doc.version = "v1"
    
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(models.Document).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # 兜底处理：确保 version 字段不为空
    if not document.version or not str(document.version).strip():
        document.version = "v1"
    
    return document


def formatVersion(v: str) -> str:
    """智能版本号格式化"""
    if not v:
        return "v1"
    version_str = str(v).strip()
    prefix_regex = re.match(r'^[vVrR]|^Rev', version_str, re.IGNORECASE)
    if prefix_regex:
        return version_str
    return f"v{version_str}"


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(document_id: int, payload: DocumentUpdate, db: Session = Depends(get_db)):
    """
    更新文档信息 - 严格按照"先做旧数据快照，再覆写数据库"的顺序
    
    业务逻辑：
    1. 从数据库获取原始数据（此时 google_drive_id 还是旧的）
    2. 保存旧值到临时变量（old_drive_id, old_version）
    3. 判断是否更换了文件（old_drive_id != new_drive_id）
    4. 用新数据覆写数据库对象
    5. 写入 ChangeLog（记录正确的 old_drive_id）
    6. 统一 commit 存盘
    """
    try:
        # Step 1: 从数据库捞出尚未被修改的原始数据
        document = db.query(models.Document).get(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Step 2: 【核心核心】在修改前，先把旧状态保存在临时变量里！！！
        old_drive_id = document.google_drive_id or ''  # 此时是 V1 的 Drive ID
        old_version = document.version or ''           # 此时是 V1
        old_title = document.title or ''
        
        # 解析前端传来的新值（增量更新：只处理非 None 的字段）
        new_drive_id_raw = payload.google_drive_id or ''
        new_drive_id = extract_drive_id(new_drive_id_raw) if new_drive_id_raw else old_drive_id
        
        # version 字段的严谨处理：如果前端传了值，使用新值；否则保留旧值
        new_version = ''
        if payload.version is not None:
            version_val = str(payload.version).strip()
            if version_val:
                new_version = version_val
            else:
                new_version = old_version
        else:
            new_version = old_version
        
        new_title = payload.title or old_title
        new_update_notes = payload.update_notes or document.update_notes or ''
        
        # 检查关联实体是否存在
        if payload.product_id is not None:
            product = db.query(models.Product).get(payload.product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
        
        if payload.bom_item_id is not None:
            bom_item = db.query(models.BOMItem).get(payload.bom_item_id)
            if not bom_item:
                raise HTTPException(status_code=404, detail="BOMItem not found")
        
        # Step 3: 对比判断，决定日志类型
        drive_id_changed = (old_drive_id != new_drive_id) and bool(new_drive_id)
        
        if drive_id_changed:
            # 情况 A: 确实更换了文件（比如 V1 升 V2）
            # 智能版本递增：如果前端传来的版本号与旧版本相同，自动加 1
            if new_version == old_version:
                new_version = bump_version(old_version)
            
            action_type = "update_file"
            change_summary = f"文件替换: {new_title} ({formatVersion(old_version)} → {formatVersion(new_version)})"
            log_details = {
                "old_drive_id": old_drive_id,   # 确保这里存的是 V1 的真正旧 ID
                "new_drive_id": new_drive_id,   # 升级后的 V2 ID
                "old_version": old_version,     # 'V1'
                "new_version": new_version,     # 'V2'
                "update_notes": new_update_notes
            }
        else:
            # 情况 B: 只是改了备注、版本名等元数据
            action_type = "update_metadata"
            change_summary = f"更新文件信息: {new_title}"
            log_details = {
                "old_version": old_version,
                "new_version": new_version,
                "update_notes": new_update_notes
            }
            # 不包含 old_drive_id，避免前端误渲染旧链接
        
        # Step 4: 这时才可以安全地用新数据覆写数据库对象
        if payload.product_id is not None:
            document.product_id = payload.product_id
        if payload.bom_item_id is not None:
            document.bom_item_id = payload.bom_item_id
        if payload.title is not None:
            document.title = payload.title
        if payload.document_type is not None:
            document.document_type = payload.document_type
        if payload.received_date is not None:
            document.received_date = payload.received_date
        if payload.version is not None:
            document.version = new_version
        if payload.google_drive_id is not None:
            document.google_drive_id = new_drive_id
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
        
        # Step 5: 写入 ChangeLog 表（在 commit 之前）
        changelog = models.ChangeLog(
            product_id=document.product_id,
            entity_type=ENTITY_TYPE_DOCUMENT,
            entity_id=document.id,
            entity_name=document.title,
            action=action_type,
            change_type="modified",
            details=log_details,
            change_summary=change_summary,
        )
        db.add(changelog)
        
        # Step 6: 统一 commit 存盘
        db.commit()
        db.refresh(document)
        
        return document
    
    except HTTPException:
        # 已经是 HTTPException，直接抛出（不回滚，因为还没修改数据）
        raise
    
    except Exception as e:
        # 发生任何意外错误，立即回滚
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"更新失败，原因: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(models.Document).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_title = document.title
    doc_drive_id = document.google_drive_id
    
    changelog = models.ChangeLog(
        product_id=document.product_id,
        entity_type=ENTITY_TYPE_DOCUMENT,
        entity_id=document.id,
        entity_name=doc_title,
        action="delete",
        change_type="deleted",
        details={"action": "delete_document", "document_title": doc_title, "google_drive_id": doc_drive_id},
        change_summary=f"删除文档: {doc_title}",
    )
    db.add(changelog)
    db.delete(document)
    db.commit()
    return None


@router.get("/{document_id}/changelog", response_model=List[ChangeLogResponse])
def get_document_changelog(document_id: int, db: Session = Depends(get_db)):
    """获取单文件的专属变更历史，按时间倒序排列"""
    document = db.query(models.Document).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    changelogs = db.query(models.ChangeLog).filter(
        models.ChangeLog.entity_type.in_([ENTITY_TYPE_DOCUMENT, "document"]),
        models.ChangeLog.entity_id == document_id
    ).order_by(models.ChangeLog.created_at.desc()).limit(50).all()
    
    return changelogs


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
