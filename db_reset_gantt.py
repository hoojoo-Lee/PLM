from sqlalchemy import text
from database import engine

print("开始重置甘特图相关表...")
with engine.connect() as conn:
    try:
        # 1. 强制删除旧的、结构不完整的表 (如果有的话)
        conn.execute(text("DROP TABLE IF EXISTS gantt_tasks CASCADE;"))
        print("已清理旧的 gantt_tasks 表。")
        
        # 2. 重新创建完全符合最新模型结构的表
        conn.execute(text("""
            CREATE TABLE gantt_tasks (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL,
                text VARCHAR NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP NOT NULL, -- 加上 end_date 以兼容部分逻辑
                duration INTEGER DEFAULT 1,
                is_workday_only BOOLEAN DEFAULT true,
                progress NUMERIC DEFAULT 0,
                dependencies TEXT DEFAULT '[]',
                assignee VARCHAR DEFAULT '',
                remark VARCHAR DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        print("✅ 新的 gantt_tasks 表创建成功，包含所有最新字段 (text, duration, is_workday_only, remark 等)！")
        
        conn.commit()
    except Exception as e:
        print(f"❌ 发生错误: {e}")