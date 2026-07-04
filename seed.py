"""
PLM 数据库初始化脚本 - 注入测试数据
用于向 Neon 云端数据库注入高还原度的硬件项目测试用例
"""

from datetime import datetime

from database import SessionLocal, engine, Base
import models


def cleanup_data(db):
    """清理旧数据，防止主键冲突"""
    print("正在清理旧数据...")
    db.query(models.BOMItem).delete()
    db.query(models.BOMVersion).delete()
    db.query(models.Document).delete()
    db.query(models.Project).delete()
    db.query(models.Product).delete()
    db.query(models.ChangeLog).delete()
    db.commit()
    print("清理完成！")


def seed_data(db):
    """注入测试数据"""
    print("开始注入测试数据...")

    # ==========================================================================
    # Product: AGX-Carrier 智能控制主板
    # ==========================================================================
    product = models.Product(
        name="AGX-Carrier 智能控制主板",
        code="AGX-CARRIER-001",
        description="用于自动驾驶路侧感知计算的核心控制主板，支持 Jetson AGX Orin 系列模组",
        status="active",
    )
    db.add(product)
    db.flush()
    print(f"  [+] Product 创建成功: {product.name} (ID: {product.id})")

    # ==========================================================================
    # BOM_Version 1: V1.0 (已封存)
    # ==========================================================================
    bom_v1 = models.BOMVersion(
        product_id=product.id,
        version_code="V1.0_Alpha",
        status="archived",
        released_at=datetime(2025, 5, 1, 10, 0, 0),
        change_notes="客户初始交付EE-BOM (2025-05-01)",
        created_by="张三",
    )
    db.add(bom_v1)
    db.flush()
    print(f"  [+] BOM_Version 创建成功: {bom_v1.version_code} (ID: {bom_v1.id})")

    # V1.0 物料明细
    items_v1 = [
        {
            "category": "EE",
            "mpn": "STM32F103RCT6",
            "name": "STM32F103RCT6 微控制器",
            "quantity": 1,
            "responsible": "张三",
            "picture_drive_id": "1-vR_k8wWvS8K6PzR2u-1hXzBvM4Qp8J9",
        },
        {
            "category": "EE",
            "mpn": "10uF 0603 16V",
            "name": "贴片电容 10uF 0603 16V X5R",
            "quantity": 5,
            "responsible": "李四",
            "picture_drive_id": None,
        },
    ]

    for item_data in items_v1:
        item = models.BOMItem(bom_version_id=bom_v1.id, **item_data)
        db.add(item)
        db.flush()
        print(f"    [-] BOM_Item 创建成功: {item_data['mpn']}")

    # ==========================================================================
    # BOM_Version 2: V2.0 (当前活动)
    # ==========================================================================
    bom_v2 = models.BOMVersion(
        product_id=product.id,
        version_code="V2.0_Beta",
        bom_type="EE",
        variant_tag="V2",
        status="active",
        released_at=datetime(2025, 6, 28, 14, 30, 0),
        change_notes="客户升级了MCU并缩小了电容封装",
        created_by="张三",
    )
    db.add(bom_v2)
    db.flush()
    print(f"  [+] BOM_Version 创建成功: {bom_v2.version_code} (ID: {bom_v2.id})")

    # V2.0 物料明细
    items_v2 = [
        {
            "category": "EE",
            "mpn": "STM32F405RGT6",
            "name": "STM32F405RGT6 微控制器 (升级版)",
            "quantity": 1,
            "responsible": "张三",
            "picture_drive_id": "1-vR_k8wWvS8K6PzR2u-1hXzBvM4Qp8J9",
        },
        {
            "category": "EE",
            "mpn": "10uF 0402 10V",
            "name": "贴片电容 10uF 0402 10V X5R (小型化)",
            "quantity": 5,
            "responsible": "李四",
            "picture_drive_id": None,
        },
        {
            "category": "EE",
            "mpn": "2.2uH 2A 顶盟",
            "name": "功率电感 2.2uH 2A SMD",
            "quantity": 1,
            "responsible": "王五",
            "picture_drive_id": None,
        },
    ]

    for item_data in items_v2:
        item = models.BOMItem(bom_version_id=bom_v2.id, **item_data)
        db.add(item)
        db.flush()
        print(f"    [-] BOM_Item 创建成功: {item_data['mpn']}")

    # ==========================================================================
    # Product 级全局文件 (测试数据)
    # ==========================================================================
    docs = [
        {
            "product_id": product.id,
            "bom_item_id": None,
            "title": "AGX-Carrier 电气原理图 V1.0",
            "document_type": "drawing",
            "category": None,
            "status": "active",
            "versions": [
                {
                    "version_number": "1.0",
                    "google_drive_id": "1Bxv8K9L2mN4pQ6rS8tU0vW1xY3zA5bC",
                    "status": "released",
                    "update_notes": "初版释放",
                }
            ]
        },
        {
            "product_id": product.id,
            "bom_item_id": None,
            "title": "产品测试规范书",
            "document_type": "test_report",
            "category": None,
            "status": "active",
            "versions": [
                {
                    "version_number": "1.0",
                    "google_drive_id": "2CxY9aB0kL3mO5pQ7rT9sU1vW2xZ4aC",
                    "status": "released",
                    "update_notes": "量产前测试标准",
                }
            ]
        },
        {
            "product_id": product.id,
            "bom_item_id": None,
            "title": "包装规范要求",
            "document_type": "package",
            "category": None,
            "status": "active",
            "versions": [
                {
                    "version_number": "1.0",
                    "google_drive_id": "3DyZ0bC1lM4nP6qR8tU2vW3xY5aB7dE",
                    "status": "draft",
                    "update_notes": "待客户确认",
                }
            ]
        },
    ]

    for doc_data in docs:
        versions_data = doc_data.pop("versions")
        doc = models.Document(**doc_data)
        db.add(doc)
        db.flush()
        
        for v_data in versions_data:
            v = models.DocumentVersion(document_id=doc.id, **v_data)
            db.add(v)
        
        print(f"    [-] Document 创建成功: {doc_data['title']}")

    db.commit()
    print("\n数据注入完成！")


def main():
    """主函数"""
    print("=" * 60)
    print("PLM 数据库初始化脚本 - 测试数据注入")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 清理旧数据
        cleanup_data(db)

        # 注入新数据
        seed_data(db)

        print("\n" + "=" * 60)
        print("所有操作已完成！请刷新前端页面查看数据。")
        print("=" * 60)

    except Exception as e:
        print(f"\n错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
