from fastapi.testclient import TestClient
from sqlalchemy import text

from main import app
from database import get_db, SessionLocal


app.dependency_overrides[get_db] = lambda: SessionLocal()


client = TestClient(app)


def test_e2e_flow():
    print("\n=== 阶段一：客户与产品流 ===")
    
    resp = client.post("/customers", json={"name": "测试客户", "status": "active"})
    assert resp.status_code == 201, f"创建客户失败: {resp.text}"
    customer = resp.json()
    print(f"创建客户成功: id={customer['id']}, name={customer['name']}")
    
    resp = client.post("/products/", json={"name": "测试产品", "code": "TEST-001"})
    assert resp.status_code == 201, f"创建产品失败: {resp.text}"
    product = resp.json()
    print(f"创建产品成功: id={product['id']}, name={product['name']}")
    
    resp = client.put(f"/products/{product['id']}", json={"customer_id": customer["id"]})
    assert resp.status_code == 200, f"更新产品 customer_id 失败: {resp.text}"
    updated_product = resp.json()
    assert updated_product["customer_id"] == customer["id"], "customer_id 更新失败"
    print(f"更新产品 customer_id 成功: customer_id={updated_product['customer_id']}")

    print("\n=== 阶段二：BOM 状态流 ===")
    
    resp = client.post(f"/products/{product['id']}/bom-versions", 
                      json={"version_code": "V1.0", "bom_type": "EE", "variant_tag": "DEFAULT"})
    assert resp.status_code == 201, f"创建 BOM 版本失败: {resp.text}"
    bom_version = resp.json()
    print(f"创建 BOM 版本成功: id={bom_version['id']}, version_code={bom_version['version_code']}")
    
    resp = client.patch(f"/products/{product['id']}/bom-versions/{bom_version['id']}/release")
    assert resp.status_code == 200, f"启用 BOM 版本失败: {resp.text}"
    released_version = resp.json()
    assert released_version["status"] == "released", "BOM 启用状态不正确"
    print(f"启用 BOM 版本成功: status={released_version['status']}")
    
    resp = client.patch(f"/products/{product['id']}/bom-versions/{bom_version['id']}/archive")
    assert resp.status_code == 200, f"封存 BOM 版本失败: {resp.text}"
    archived_version = resp.json()
    assert archived_version["status"] == "archived", "BOM 封存状态不正确"
    print(f"封存 BOM 版本成功: status={archived_version['status']}")

    print("\n=== 阶段三：文控流 ===")
    
    resp = client.post(f"/products/{product['id']}/documents", 
                      json={"title": "产品测试规范书", "document_type": "spec", "category": "engineering", "status": "active"})
    assert resp.status_code == 201, f"创建文档失败: {resp.text}"
    document = resp.json()
    print(f"创建文档成功: id={document['id']}, title={document['title']}")
    
    resp = client.post(f"/products/{product['id']}/documents/{document['id']}/versions",
                      json={
                          "version_number": "1.0",
                          "received_date": "2026-07-05",
                          "google_drive_id": "test-drive-id-123",
                          "file_name": "产品测试规范书_V1.0.pdf",
                          "file_size": 1024000,
                          "mime_type": "application/pdf",
                          "responsible": "张三",
                          "status": "active",
                          "update_notes": "初始版本"
                      })
    assert resp.status_code == 201, f"创建文档版本失败: {resp.text}"
    doc_version = resp.json()
    print(f"创建文档版本成功: id={doc_version['id']}, version={doc_version['version_number']}")
    
    resp = client.get(f"/products/{product['id']}/documents/{document['id']}")
    assert resp.status_code == 200, f"获取文档详情失败: {resp.text}"
    doc_detail = resp.json()
    assert "latest_version" in doc_detail, "文档详情缺少 latest_version"
    assert doc_detail["latest_version"]["version_number"] == "1.0", "latest_version 版本号不正确"
    print(f"验证文档详情成功: latest_version={doc_detail['latest_version']['version_number']}")

    print("\n=== 阶段四：项目与 NPI 流 ===")
    
    resp = client.post(f"/products/{product['id']}/projects",
                      json={"name": "测试项目", "code": "PRJ-001", "current_stage": "S1"})
    assert resp.status_code == 201, f"创建项目失败: {resp.text}"
    project = resp.json()
    print(f"创建项目成功: id={project['id']}, name={project['name']}")
    
    resp_npi = client.post("/api/npi-categories", 
                          json={"name": "测试类别", "description": "测试", "applicable_stages": "proto,dvt,pvt,mp"})
    assert resp_npi.status_code == 201, f"创建 NPI Category 失败: {resp_npi.text}"
    category = resp_npi.json()
    print(f"创建 NPI Category 成功: id={category['id']}")
    
    resp = client.post(f"/products/{product['id']}/tracker-tasks",
                      json={
                          "category_id": category["id"],
                          "stage": "proto",
                          "task_description": "测试任务描述",
                          "project_id": project["id"],
                          "owner": "李四",
                          "priority": "P1",
                          "status": "pending"
                      })
    assert resp.status_code == 201, f"创建 Tracker 任务失败: {resp.text}"
    tracker_task = resp.json()
    assert tracker_task["project_id"] == project["id"], "Tracker 任务 project_id 不正确"
    print(f"创建 Tracker 任务成功: id={tracker_task['id']}, project_id={tracker_task['project_id']}")

    print("\n=== 阶段五：甘特联动流 ===")
    
    resp = client.post(f"/products/{product['id']}/tracker-tasks/{tracker_task['id']}/sync-to-gantt",
                      json={"start_date": "2026-07-05", "duration": 5, "assignee": "王五"})
    assert resp.status_code == 200, f"同步到甘特图失败: {resp.text}"
    sync_result = resp.json()
    assert "gantt_task_id" in sync_result, "同步结果缺少 gantt_task_id"
    print(f"同步到甘特图成功: gantt_task_id={sync_result['gantt_task_id']}")
    
    resp = client.get(f"/products/{product['id']}/gantt-tasks")
    assert resp.status_code == 200, f"获取甘特任务失败: {resp.text}"
    gantt_tasks = resp.json()
    assert len(gantt_tasks) == 1, f"甘特任务数量不正确: {len(gantt_tasks)}"
    assert gantt_tasks[0]["task_text"] == "测试任务描述", "甘特任务文本不正确"
    print(f"验证甘特任务成功: task_text={gantt_tasks[0]['task_text']}")
    
    resp = client.get(f"/products/{product['id']}/tracker-tasks/{tracker_task['id']}")
    assert resp.status_code == 200, f"获取 Tracker 任务失败: {resp.text}"
    updated_tracker = resp.json()
    assert updated_tracker["gantt_task_id"] == sync_result["gantt_task_id"], "Tracker 任务 gantt_task_id 未更新"
    print(f"验证 Tracker 任务 gantt_task_id 更新成功: {updated_tracker['gantt_task_id']}")

    print("\n=== 所有测试通过 ===")
    
    print("\n=== 清理测试数据 ===")
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM tracker_tasks WHERE task_description = '测试任务描述'"))
        db.execute(text("DELETE FROM gantt_tasks WHERE task_text = '测试任务描述'"))
        db.execute(text("DELETE FROM document_versions WHERE file_name = '产品测试规范书_V1.0.pdf'"))
        db.execute(text("DELETE FROM documents WHERE title = '产品测试规范书'"))
        db.execute(text("DELETE FROM projects WHERE code = 'PRJ-001'"))
        db.execute(text("DELETE FROM npi_categories WHERE name = '测试类别'"))
        db.execute(text("DELETE FROM bom_items WHERE bom_version_id IN (SELECT id FROM bom_versions WHERE version_code = 'V1.0')"))
        db.execute(text("DELETE FROM bom_versions WHERE version_code = 'V1.0'"))
        db.execute(text("DELETE FROM products WHERE code = 'TEST-001'"))
        db.execute(text("DELETE FROM customers WHERE name = '测试客户'"))
        db.commit()
        print("清理完成")
    finally:
        db.close()


if __name__ == "__main__":
    test_e2e_flow()