"""
Semtech SX9331Q/WQ PCBA 项目数据注入脚本
向 Neon 云端数据库写入新项目数据，用于前端全流程调试
"""

from datetime import datetime

from database import SessionLocal
import models


def add_semtech_project(db):
    """注入 Semtech SX9331Q/WQ PCBA 项目数据"""
    print("开始注入 Semtech SX9331Q/WQ 项目数据...")

    # ==========================================================================
    # Product: Semtech SX9331Q/WQ
    # ==========================================================================
    product = models.Product(
        name="Semtech SX9331Q/WQ",
        code="SEMTECH-SX9331",
        description="纯 PCBA 研发项目 - 智能射频控制主板",
        status="active",
    )
    db.add(product)
    db.flush()
    print(f"  [+] Product 创建成功: {product.name} (ID: {product.id})")

    # ==========================================================================
    # BOM_Version: V1.0_Init
    # ==========================================================================
    bom_version = models.BOMVersion(
        product_id=product.id,
        version_code="V1.0_Init",
        status="active",
        received_at=datetime.now(),
        change_notes="项目初始化，优先调通甘特图、Todo List 及文控 Design File 模块",
        created_by="系统自动注入",
    )
    db.add(bom_version)
    db.flush()
    print(f"  [+] BOM_Version 创建成功: {bom_version.version_code} (ID: {bom_version.id})")

    # ==========================================================================
    # BOM_Item: SX9331Q/WQ 主板核心板
    # ==========================================================================
    bom_item = models.BOMItem(
        bom_version_id=bom_version.id,
        category="PCBA",
        name="SX9331Q/WQ 主板核心板",
        mpn="SX9331Q/WQ-MAIN-BRD",
        quantity=1,
        designator="MAIN",
        responsible="未分配",
        status="engineering",
        picture_drive_id="",  # 留空，等用户在前端可视化补全
    )
    db.add(bom_item)
    db.flush()
    print(f"  [+] BOM_Item 创建成功: {bom_item.name} (ID: {bom_item.id})")

    db.commit()
    print("\n项目数据注入完成！")


def main():
    """主函数"""
    print("=" * 60)
    print("Semtech SX9331Q/WQ PCBA 项目数据注入脚本")
    print("=" * 60)

    db = SessionLocal()
    try:
        add_semtech_project(db)

        print("\n" + "=" * 60)
        print("所有操作已完成！请刷新前端页面查看新项目。")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()