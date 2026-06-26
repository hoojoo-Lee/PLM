\# 个人轻量级 PLM 系统开发备忘录


## 1. 技术栈
- 数据库：PostgreSQL
- 文件存储：Google Drive API (仅存储 File ID)
- 后端：Python (FastAPI + SQLAlchemy)
- 前端：[待定，如 Vue3 或 React]


\## 2. 核心设计原则

\- \*\*强关联\*\*：以项目为主线，图纸/文件为核心，BOM 和物料联动。

\- \*\*低颗粒度\*\*：抛弃复杂的审批流，采用单版本覆盖 + 线性历史记录。

\- \*\*自动化 Tracker\*\*：任何实体的增删改操作，都要自动向 `change\_log` 表写入 JSONB 格式的差异记录。



\## 3. 核心业务实体

1\. Project (项目) \& Issue (质量/缺陷追踪)

2\. Part (物料主数据)

3\. BOM (多层级物料清单，通过递归查询构建)

4\. Document (图纸/规格书，必须包含 google\_drive\_file\_id 字段)

5\. ChangeLog (自动化变更流水)

## 4. 全局业务逻辑与目标模式对齐 (基于 Control Book 表格逻辑)

### 模块 A：项目进度与风险主线 (Project & Progress & Risk)
- **项目表 (Project)**：管理全局项目。
- **进度表 (Timeline/Milestone)**：替代 Excel 里的 Gantt/Timeline，记录项目的关键节点（如 EVT, DVT, S1, S2 阶段）和预计/实际完成时间。
- **风险与追踪 (Issue/RiskTracker)**：替代 Excel 里的 Risk List，记录跟进事项，必须关联到具体的 Project，且可选关联具体的 Part。

### 模块 B：扁平化物料管理 (Flat Part List)
- **抛弃复杂 BOM 树**：物料不需要复杂的父子层级，只需通过 `project_id` 和 `category` (如 EE-BOM, ME-BOM, PKG-BOM) 扁平化挂载在项目下。
- **关键字段对齐**：必须包含产品图 (Picture Drive ID)、MPN、内部料号、负责人 (Responsible)、定型状态 (Design finalization) 以及交期 (Lead Time)。

### 模块 C：文件版本与预览核心 (Document & Versioning)
- **图纸归档**：Document 直接挂载在 Part 下。
- **强制版本记录**：每次上传新图纸或更新链接，必须带上 Version 号和更新说明 (Update Notes)。
- **在线预览**：强依赖 Google Drive API 的 File ID，前端能够直接调用预览产品图和 PDF/图纸。

### 模块 D：自动化更新日志 (Auto-ChangeLog)
- **无需手动写流水**：任何人（或你自己）修改了 Part 的状态、更新了 Document 的版本、或者推进了 Timeline，系统在后端（FastAPI 拦截器）自动生成一条日志记录。
- **日志展示**：在项目主页和物料主页，可以直接渲染出类似“朋友圈”的时间轴，清晰显示“什么时间、谁、把设计版本从 V1 更新到了 V2”。