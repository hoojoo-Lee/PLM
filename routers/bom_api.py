from typing import List
import json
import os
import re
import shutil
import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
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
    ChangeLogResponse,
    DocumentResponse,
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


@router.get("/versions/{version_id}/documents", response_model=List[DocumentResponse])
def get_bom_version_documents(version_id: int, db: Session = Depends(get_db)):
    version = db.query(models.BOMVersion).get(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    documents = db.query(models.Document).filter(
        models.Document.bom_version_id == version_id
    ).all()
    return documents


@router.get("/versions/{version_id}/aggregated-changelogs")
def get_aggregated_changelogs(version_id: int, db: Session = Depends(get_db)):
    """聚合查询：返回指定 BOM 版本下所有物料的变更日志"""
    version = db.query(models.BOMVersion).get(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")

    # 查出该版本下所有物料 ID
    item_ids = [row[0] for row in db.query(models.BOMItem.id).filter(
        models.BOMItem.bom_version_id == version_id
    ).all()]

    if not item_ids:
        return []

    # 聚合查询所有关联的变更日志，按时间倒序
    changelogs = db.query(models.ChangeLog).filter(
        models.ChangeLog.entity_type == "bom_item",
        models.ChangeLog.entity_id.in_(item_ids)
    ).order_by(models.ChangeLog.created_at.desc()).limit(200).all()

    # 构建物料 ID -> (name, mpn) 的映射
    items = db.query(models.BOMItem).filter(
        models.BOMItem.id.in_(item_ids)
    ).all()
    item_map = {item.id: {"name": item.name, "mpn": item.mpn} for item in items}

    result = []
    for cl in changelogs:
        info = item_map.get(cl.entity_id, {"name": "未知", "mpn": "-"})
        detail = {}
        if cl.change_detail:
            try:
                detail = json.loads(cl.change_detail)
            except (json.JSONDecodeError, TypeError):
                detail = {}
        result.append({
            "id": cl.id,
            "created_at": cl.created_at.isoformat() if cl.created_at else None,
            "change_type": cl.change_type,
            "change_summary": cl.change_summary,
            "action": detail.get("action", ""),
            "item_name": info["name"],
            "item_mpn": info["mpn"],
            "item_id": cl.entity_id,
            "old_version": detail.get("old_version", ""),
            "new_version": detail.get("new_version", ""),
        })
    return result


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
        responsible_party=payload.responsible_party or 'NexPCB',
        mpn=payload.mpn,
        name=payload.name,
        quantity=payload.quantity,
        responsible=payload.responsible,
        status=payload.status,
        picture_drive_id=payload.picture_drive_id,
        design_files=payload.design_files or [],
        sort_order=payload.sort_order or 0,
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


@router.put("/items/reorder", response_model=dict)
def reorder_bom_items(payload: list[dict], db: Session = Depends(get_db)):
    """批量更新物料排序 {id, sort_order}"""
    for item_data in payload:
        item = db.query(models.BOMItem).get(item_data.get("id"))
        if item:
            item.sort_order = item_data.get("sort_order", 0)
    db.commit()
    return {"status": "ok"}


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

    old_picture_id = item.picture_drive_id
    old_design_files = item.design_files or []

    if payload.bom_version_id is not None:
        bom_version = db.query(models.BOMVersion).get(payload.bom_version_id)
        if not bom_version:
            raise HTTPException(status_code=404, detail="BOMVersion not found")
        item.bom_version_id = payload.bom_version_id
    if payload.category is not None:
        item.category = payload.category
    if payload.responsible_party is not None:
        item.responsible_party = payload.responsible_party
    if payload.mpn is not None:
        item.mpn = payload.mpn
    if payload.name is not None:
        item.name = payload.name
    if payload.quantity is not None:
        item.quantity = payload.quantity
    if payload.responsible is not None:
        item.responsible = payload.responsible
    if payload.status is not None:
        item.status = payload.status
    if payload.picture_drive_id is not None:
        new_picture_id = _extract_drive_id(payload.picture_drive_id)
        item.picture_drive_id = new_picture_id
    if payload.design_files is not None:
        item.design_files = payload.design_files
    if payload.sort_order is not None:
        item.sort_order = payload.sort_order

    try:
        db.add(item)
        db.commit()
        db.refresh(item)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

    # 精准日志：预览图变更
    if payload.picture_drive_id is not None and old_picture_id != item.picture_drive_id:
        changelog = models.ChangeLog(
            entity_type="bom_item",
            entity_id=item.id,
            entity_name=item.name,
            change_type="update",
            change_summary=f"更新预览图: {item.name}",
            change_detail=json.dumps({"action": "update_picture", "old_picture_id": old_picture_id, "new_picture_id": item.picture_drive_id}),
        )
        db.add(changelog)
        db.commit()

    # 精准日志：design_files 差异对比
    if payload.design_files is not None:
        new_design_files = payload.design_files
        old_map = {f.get("file_type"): f for f in old_design_files}
        new_map = {f.get("file_type"): f for f in new_design_files}

        for ft, new_file in new_map.items():
            old_file = old_map.get(ft)
            if old_file is None:
                # 新增设计文件
                changelog = models.ChangeLog(
                    entity_type="bom_item",
                    entity_id=item.id,
                    entity_name=item.name,
                    change_type="update",
                    change_summary=f"新增设计文件: {item.name} - {ft}",
                    change_detail=json.dumps({"action": "add_design_file", "file_type": ft, "drive_id": new_file.get("drive_id"), "version": new_file.get("version")}),
                )
                db.add(changelog)
            elif old_file.get("drive_id") != new_file.get("drive_id"):
                # 设计文件替换（精准追溯）
                changelog = models.ChangeLog(
                    entity_type="bom_item",
                    entity_id=item.id,
                    entity_name=item.name,
                    change_type="update",
                    change_summary=f"设计文件升版: {item.name} - {ft} {old_file.get('version','')} -> {new_file.get('version','')}",
                    change_detail=json.dumps({
                        "action": "update_design_file",
                        "file_type": ft,
                        "old_drive_id": old_file.get("drive_id"),
                        "new_drive_id": new_file.get("drive_id"),
                        "old_version": old_file.get("version"),
                        "new_version": new_file.get("version"),
                    }),
                )
                db.add(changelog)

        # 检查被删除的文件类型
        for ft in old_map:
            if ft not in new_map:
                changelog = models.ChangeLog(
                    entity_type="bom_item",
                    entity_id=item.id,
                    entity_name=item.name,
                    change_type="update",
                    change_summary=f"删除设计文件: {item.name} - {ft}",
                    change_detail=json.dumps({"action": "remove_design_file", "file_type": ft}),
                )
                db.add(changelog)

        db.commit()

    return item


@router.get("/items/{item_id}/changelog", response_model=List[ChangeLogResponse])
def get_bom_item_changelog(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.BOMItem).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="BOMItem not found")
    changelogs = db.query(models.ChangeLog).filter(
        models.ChangeLog.entity_type == "bom_item",
        models.ChangeLog.entity_id == item_id
    ).order_by(models.ChangeLog.created_at.desc()).limit(50).all()
    return changelogs


def _extract_drive_id(input_str: str) -> str:
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


@router.post("/items/{item_id}/upload-picture", response_model=BOMItemResponse)
def upload_bom_item_picture(item_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    item = db.query(models.BOMItem).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="BOMItem not found")

    try:
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        # 生成唯一文件名防止覆盖
        ext = os.path.splitext(file.filename or "image.png")[1] or ".png"
        filename = f"{int(time.time())}_{item_id}{ext}"
        file_path = os.path.join(upload_dir, filename)

        # 保存物理文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 更新数据库，存入相对路径
        old_picture_id = item.picture_drive_id
        relative_path = f"/uploads/{filename}"
        item.picture_drive_id = relative_path
        db.add(item)
        db.commit()
        db.refresh(item)

        changelog = models.ChangeLog(
            entity_type="bom_item",
            entity_id=item.id,
            entity_name=item.name,
            change_type="update",
            change_summary=f"更新预览图: {item.name}",
            change_detail=json.dumps({"action": "update_picture", "old_picture_id": old_picture_id, "new_picture_id": relative_path, "filename": filename}),
        )
        db.add(changelog)
        db.commit()

        return item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")


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
            responsible_party=payload.responsible_party or 'NexPCB',
            mpn=payload.mpn,
            name=payload.name,
            quantity=payload.quantity,
            responsible=payload.responsible,
            status=payload.status,
            picture_drive_id=payload.picture_drive_id,
            design_files=payload.design_files or [],
        )
        db.add(bom_item)
        created_items.append(bom_item)
    
    db.commit()
    for item in created_items:
        db.refresh(item)
    
    return created_items


@router.post("/import/{bom_version_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
def import_bom_from_excel(bom_version_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    bom_version = db.query(models.BOMVersion).get(bom_version_id)
    if not bom_version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    
    allowed_extensions = ['.xlsx', '.xls', '.csv']
    filename = file.filename.lower()
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Only Excel (.xlsx, .xls) or CSV files are allowed")
    
    try:
        if filename.endswith('.csv'):
            import csv
            content = file.file.read().decode('utf-8').strip()
            lines = content.split('\n')
            reader = csv.DictReader(lines)
            rows = list(reader)
        else:
            from io import BytesIO
            import openpyxl
            wb = openpyxl.load_workbook(BytesIO(file.file.read()), data_only=True)
            ws = wb.active
            headers = [cell.value for cell in ws[1]]
            rows = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if all(cell is None for cell in row):
                    continue
                rows.append(dict(zip(headers, row)))
        
        column_mapping = {
            'mpn': ['mpn', '料号', '物料编号', 'part number', 'pn', '编号'],
            'name': ['name', '物料名称', '名称', '品名', 'description', '描述'],
            'quantity': ['quantity', '数量', '用量', 'qty'],
            'category': ['category', '分类', '类别', '类型'],
            'responsible_party': ['responsible_party', '责任方', '模块', '板卡', '所属板卡', '所属模块'],
            'responsible': ['responsible', '负责人', '责任人'],
            'status': ['status', '状态'],
        }
        
        def find_column(header, candidates):
            if not header:
                return None
            h = str(header).strip().lower()
            for candidate in candidates:
                if candidate.lower() in h or h in candidate.lower():
                    return h
            return None
        
        col_indices = {}
        if rows:
            first_row = rows[0]
            for key, candidates in column_mapping.items():
                for header in first_row.keys():
                    if find_column(header, candidates):
                        col_indices[key] = header
                        break
        
        created_count = 0
        skipped_count = 0
        
        for row in rows:
            mpn = str(row.get(col_indices.get('mpn'))).strip() if col_indices.get('mpn') else ''
            name = str(row.get(col_indices.get('name'))).strip() if col_indices.get('name') else ''
            
            if not mpn and not name:
                skipped_count += 1
                continue
            
            quantity = row.get(col_indices.get('quantity'))
            try:
                quantity = int(quantity) if quantity else 1
            except ValueError:
                quantity = 1
            
            category = str(row.get(col_indices.get('category'))).strip() if col_indices.get('category') else ''
            responsible_party = str(row.get(col_indices.get('responsible_party'))).strip() if col_indices.get('responsible_party') else ''
            responsible = str(row.get(col_indices.get('responsible'))).strip() if col_indices.get('responsible') else ''
            status = str(row.get(col_indices.get('status'))).strip() if col_indices.get('status') else 'pending'
            
            if not name:
                name = mpn
            
            bom_item = models.BOMItem(
                bom_version_id=bom_version_id,
                category=category,
                responsible_party=responsible_party,
                mpn=mpn,
                name=name,
                quantity=quantity,
                responsible=responsible,
                status=status,
            )
            db.add(bom_item)
            created_count += 1
        
        db.commit()
        
        return {
            'message': f'BOM 导入成功',
            'created_count': created_count,
            'skipped_count': skipped_count,
            'column_mapping': col_indices,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
