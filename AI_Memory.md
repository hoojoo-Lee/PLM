# PLM System Architecture & Development Constraints (V1.0)

## 一、开发者行为准则 (Developer Behavioral Code)
1. **绝不造轮子**：尽最大可能调用成熟的 npm 包（如 Element Plus, 成熟的 Gantt 库）和 Python 库。首要保证开发速度和系统稳定性。
2. **意图大于字面指令**：PO 负责提供业务蓝图，可能缺乏底层代码细节。如果发现技术指令有漏洞、性能隐患或有更好的开源方案，绝不要盲目执行。请主动理解业务意图，纠正技术错误，并给出最优工程路径。

## 二、核心业务纪律与底层模型
1. **绝对主键**：`product_id` 是系统唯一的数据挂载中心。
2. **BOM 变体与防呆**：不建独立的 SKU 表。在 `bom_versions` 表增加 `bom_type` 和 `variant_tag`。前端不硬性锁死 Released 的 BOM，后端靠 `change_logs` 静默捕捉 JSON Diff。
3. **松散耦合与文控血脉**：`tracker_tasks` 中保留可为空的 `gantt_task_id` 实现软关联。文控模块严格遵守 `documents` -> `document_versions` 父子结构。

## 三、核心架构红线 (Architecture Rules)
- **绝对主键**：`product_id` 是系统唯一的数据隔离与挂载中心。任何新表必须带 `product_id`。
- **不建 SKU 表**：通过 `bom_versions` 表中的 `bom_type` (EE/ME/PKG) 和 `variant_tag` (如 Base) 来实现软性变体。
- **柔性防呆**：BOM 即使在 `Released` 状态，前端依然允许用户编辑。后端依赖 `change_logs` 捕捉 diff_data，严禁做硬性 403 拦截。
- **单向软绑定**：NPI 任务 (`tracker_tasks`) 与 `gantt_tasks` 是松散耦合。`tracker_tasks` 中包含可为空的 `gantt_task_id`。
- **文控血脉**：文件管理严格遵守 `documents` (逻辑主体) -> `document_versions` (物理文件版本) 的父子级结构。

## 四、数据库设计防御 (Database Constraints)
- **BOM 版本防冲突**：在 `bom_versions` 中，联合字段 `[product_id, bom_type, variant_tag, version]` 必须建立 Unique 约束。
- **JSON Diff 规范**：`change_logs` 的 `diff_data` 必须是结构化的，格式要求为：`{"field": "quantity", "old": 5, "new": 6}`。

## 五、终极数据架构 ER 图 (Mermaid)
```mermaid
erDiagram
    CUSTOMERS ||--o{ PRODUCTS : owns
    PRODUCTS ||--o{ BOM_VERSIONS : has
    PRODUCTS ||--o{ GANTT_TASKS : schedules
    PRODUCTS ||--o{ TRACKER_TASKS : tracks
    PRODUCTS ||--o{ RISKS : faces
    PRODUCTS ||--o{ DOCUMENTS : manages
    BOM_VERSIONS ||--o{ BOM_ITEMS : contains
    BOM_ITEMS ||--o{ CHANGE_LOGS : triggers
    GANTT_TASKS |o--o{ TRACKER_TASKS : soft_sync
    DOCUMENTS ||--o{ DOCUMENT_VERSIONS : maintains

    BOM_VERSIONS {
        string bom_type
        string variant_tag
        string status
    }
    BOM_ITEMS {
        string ref_des
        string footprint
    }
    TRACKER_TASKS {
        int gantt_task_id FK
        string category
        string status
    }
```

## 六、开发路线图 (Development Roadmap)
*(待补充)*
