from typing import List

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
        sub_module=payload.sub_module or '',
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
    if payload.sub_module is not None:
        item.sub_module = payload.sub_module
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


@router.post("/import/{bom_version_id}", response_model=dict, status_code=status.HTTP_201_CREATED)
def import_bom_from_excel(bom_version_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    智能解析 Excel BOM 文件并批量导入
    
    特性：
    1. 智能表头寻找：自动识别真实表头行（跳过项目信息描述行）
    2. 列名模糊匹配：支持中英文多种列名写法
    3. 全局异常捕获：友好返回 400 错误而非 500
    """
    bom_version = db.query(models.BOMVersion).get(bom_version_id)
    if not bom_version:
        raise HTTPException(status_code=404, detail="BOMVersion not found")
    
    allowed_extensions = ['.xlsx', '.xls', '.csv']
    filename = file.filename.lower() if file.filename else ''
    if not any(filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="仅支持 Excel (.xlsx, .xls) 或 CSV 文件格式")
    
    try:
        from io import BytesIO
        import pandas as pd
        
        file_content = file.file.read()
        file_bytes = BytesIO(file_content)
        
        # =========================================================================
        # Step 1: 智能寻找表头行 (Header Row Detection)
        # =========================================================================
        header_row_index = 0  # 默认表头在第 0 行
        
        if not filename.endswith('.csv'):
            # 先读取整个文件，不带表头
            try:
                df_raw = pd.read_excel(file_bytes, header=None, engine='openpyxl', dtype=str)
            except Exception as read_err:
                raise HTTPException(status_code=400, detail=f"Excel 文件读取失败: {str(read_err)}")
            
            # 遍历前 20 行，查找包含核心 BOM 关键字的行
            mpn_keywords = ['mpn', 'part number', 'partnumber', 'mfg part number', '制造料号', '料号', '物料编号', 'pn']
            designator_keywords = ['designator', 'reference', 'ref', 'ref des', '位号', '位置', '参考']
            
            for row_idx in range(min(20, len(df_raw))):
                row_values = df_raw.iloc[row_idx].astype(str).str.lower().str.strip()
                row_text = ' '.join(row_values.tolist())
                
                # 检查是否同时包含 MPN 和 Designator 相关关键字
                has_mpn_keyword = any(kw in row_text for kw in mpn_keywords)
                has_designator_keyword = any(kw in row_text for kw in designator_keywords)
                
                if has_mpn_keyword and has_designator_keyword:
                    header_row_index = row_idx
                    break
        
        # =========================================================================
        # Step 2: 重新读取文件，使用正确的表头行
        # =========================================================================
        file_bytes.seek(0)  # 重置文件指针
        
        if filename.endswith('.csv'):
            df = pd.read_csv(file_bytes, dtype=str)
        else:
            df = pd.read_excel(file_bytes, header=header_row_index, engine='openpyxl', dtype=str)
        
        # 清理数据
        df = df.dropna(how='all')  # 删除全空行
        df = df.fillna('')  # 空值填充为空字符串
        
        # 清理列名：去除首尾空格、换行符
        df.columns = [str(col).strip().replace('\n', '').replace('\r', '') for col in df.columns]
        
        # =========================================================================
        # Step 3: 增强的列名模糊匹配
        # =========================================================================
        column_mapping = {
            'mpn': ['mpn', 'part number', 'partnumber', 'mfg part number', '制造料号', '料号', '物料编号', 'pn', 'manufacturer part number', '厂商料号'],
            'designator': ['designator', 'reference', 'ref', 'ref des', '位号', '位置', '参考', 'ref designator', 'reference designator'],
            'quantity': ['quantity', 'qty', '用量', '数量', 'count', 'amount', 'qty per unit', '每台用量'],
            'name': ['name', 'description', '名称', '描述', '规格', 'specification', 'spec', 'part name', '物料名称', '品名'],
            'category': ['category', '分类', '类型', '类别', 'type', 'item type', '物料分类'],
            'responsible': ['responsible', '负责人', '责任人', 'owner', '采购负责人', 'engineer'],
            'status': ['status', '状态', '物料状态', 'item status', 'lifecycle status'],
            'picture_drive_id': ['picture_drive_id', '图片', 'drive id', 'google drive id', 'image id', '图片链接', 'photo'],
        }
        
        def find_column_mapping(df_columns, candidates):
            """模糊匹配列名"""
            for df_col in df_columns:
                col_lower = str(df_col).lower().strip()
                for candidate in candidates:
                    candidate_lower = candidate.lower().strip()
                    # 完全匹配或包含匹配
                    if col_lower == candidate_lower or candidate_lower in col_lower or col_lower in candidate_lower:
                        return df_col
            return None
        
        col_indices = {}
        for key, candidates in column_mapping.items():
            matched_col = find_column_mapping(df.columns, candidates)
            if matched_col:
                col_indices[key] = matched_col
        
        # 检查必填列是否存在
        if 'mpn' not in col_indices:
            raise HTTPException(
                status_code=400, 
                detail=f"BOM 解析失败：未找到 MPN（料号）列。请确保 Excel 表头包含以下关键字之一：{column_mapping['mpn']}。当前识别到的列名：{list(df.columns)}"
            )
        
        # =========================================================================
        # Step 4: 批量导入物料
        # =========================================================================
        created_count = 0
        skipped_count = 0
        warnings = []
        
        for idx, row in df.iterrows():
            try:
                mpn = str(row.get(col_indices.get('mpn'), '')).strip()
                
                if not mpn:
                    skipped_count += 1
                    if len(warnings) < 10:
                        warnings.append(f"第 {idx + header_row_index + 2} 行: 缺少必填项 MPN（料号），已跳过")
                    continue
                
                name = str(row.get(col_indices.get('name', col_indices.get('mpn')), '')).strip()
                if not name:
                    name = mpn
                
                quantity_val = row.get(col_indices.get('quantity'))
                try:
                    quantity = int(float(quantity_val)) if quantity_val and str(quantity_val).strip() else 1
                except (ValueError, TypeError):
                    quantity = 1
                
                designator = str(row.get(col_indices.get('designator'), '')).strip()
                category = str(row.get(col_indices.get('category'), '')).strip()
                responsible = str(row.get(col_indices.get('responsible'), '')).strip()
                status_val = str(row.get(col_indices.get('status'), '')).strip().lower() or 'engineering'
                picture_drive_id = str(row.get(col_indices.get('picture_drive_id'), '')).strip()
                
                bom_item = models.BOMItem(
                    bom_version_id=bom_version_id,
                    category=category,
                    mpn=mpn,
                    name=name,
                    quantity=quantity,
                    designator=designator,
                    responsible=responsible,
                    status=status_val,
                    picture_drive_id=picture_drive_id,
                )
                db.add(bom_item)
                created_count += 1
                
            except Exception as row_err:
                skipped_count += 1
                if len(warnings) < 10:
                    warnings.append(f"第 {idx + header_row_index + 2} 行解析失败: {str(row_err)}")
        
        db.commit()
        
        result = {
            'message': f'BOM 导入成功',
            'created_count': created_count,
            'skipped_count': skipped_count,
            'header_row_index': header_row_index,
            'column_mapping': col_indices,
            'detected_columns': list(df.columns),
        }
        
        if warnings:
            result['warnings'] = warnings
        
        return result
    
    except ImportError as e:
        raise HTTPException(status_code=400, detail=f"缺少依赖库，请安装 pandas 和 openpyxl: {str(e)}")
    
    except HTTPException:
        # 已经是 HTTPException，直接抛出
        raise
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"BOM 解析失败，请检查 Excel 格式。系统报错信息: {str(e)}"
        )
