"""
数据库迁移脚本 - 更新 ChangeLog 表结构
添加 product_id 和 details (JSONB) 字段
"""

from sqlalchemy import text
from database import SessionLocal, engine


def migrate_changelog_table():
    """迁移 ChangeLog 表结构"""
    print("开始迁移 change_logs 表...")

    db = SessionLocal()
    try:
        # 添加 product_id 列（如果不存在）
        try:
            db.execute(text("""
                ALTER TABLE change_logs 
                ADD COLUMN IF NOT EXISTS product_id BIGINT 
                REFERENCES products(id) ON DELETE SET NULL
            """))
            print("  [+] 添加 product_id 列成功")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e):
                print("  [i] product_id 列已存在，跳过")
            else:
                raise

        # 添加 action 列（如果不存在）
        try:
            db.execute(text("""
                ALTER TABLE change_logs 
                ADD COLUMN IF NOT EXISTS action VARCHAR(20)
            """))
            print("  [+] 添加 action 列成功")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e):
                print("  [i] action 列已存在，跳过")
            else:
                raise

        # 添加 details 列（JSONB 类型）
        try:
            db.execute(text("""
                ALTER TABLE change_logs 
                ADD COLUMN IF NOT EXISTS details JSONB
            """))
            print("  [+] 添加 details (JSONB) 列成功")
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e):
                print("  [i] details 列已存在，跳过")
            else:
                raise

        # 将旧数据迁移：从 change_type 复制到 action
        try:
            db.execute(text("""
                UPDATE change_logs 
                SET action = change_type 
                WHERE action IS NULL AND change_type IS NOT NULL
            """))
            print("  [+] 迁移 change_type -> action 数据成功")
        except Exception as e:
            print(f"  [w] 迁移数据时出错: {e}")

        # 将旧的 change_detail (String) 转换为 details (JSONB)
        try:
            db.execute(text("""
                UPDATE change_logs 
                SET details = change_detail::jsonb 
                WHERE details IS NULL AND change_detail IS NOT NULL
            """))
            print("  [+] 迁移 change_detail -> details 数据成功")
        except Exception as e:
            print(f"  [w] 迁移 JSON 数据时出错: {e}")

        db.commit()
        print("\n迁移完成！")

    except Exception as e:
        print(f"\n错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("数据库迁移脚本 - 更新 ChangeLog 表结构")
    print("=" * 60)

    migrate_changelog_table()

    print("\n" + "=" * 60)
    print("迁移完成！请重启后端服务。")
    print("=" * 60)


if __name__ == "__main__":
    main()