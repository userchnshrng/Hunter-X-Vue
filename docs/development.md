# 本地使用与开发

## 当前能力

阶段 A 提供真实登录、公司及来源资料、职位、人才、履历追加、沟通追加、职位推荐状态、私有附件上传下载。使用本地 SQLite，重启不丢数据。

阶段 B 已提供 Excel/CSV 导入、自定义字段管理、逐条编辑与筛选。PDF/Word/OCR 文字提取、DeepSeek 匹配和话术尚未接入，属于后续阶段。现在上传附件只保存原件，不会解析或调用 AI。

工作台仅用于电脑浏览器，手机导航抽屉、手机专用样式及手机测试已移除。桌面覆盖 1024/1280/1440/1920 px 和 1280 × 720 较矮窗口；规则、调整清单与实际验收结果见 [桌面范围调整](desktop-scope-plan.md)。

## 首次登录

本工作区的项目依赖和空数据库已准备好，没有演示账号。请打开 PowerShell，输入：

```powershell
cd D:\program\Hunter-X-Vue\backend
.\.venv\Scripts\python.exe -X utf8 -m app.cli create-admin
```

按提示设置至少 12 位的密码（输入不显示），默认用户名 `admin`。密码不需要发到聊天。命令不会覆盖已有用户名。

## 启动服务

本次 Codex 已启动本地服务；如果能打开工作台，无需重复启动。以后服务停止时按以下步骤重新运行。

后端，一个 PowerShell 窗口：

```powershell
cd D:\program\Hunter-X-Vue\backend
.\.venv\Scripts\python.exe -X utf8 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

前端，另一个 PowerShell 窗口：

```powershell
cd D:\program\Hunter-X-Vue\frontend
pnpm dev
```

打开 [本地工作台](http://127.0.0.1:8848)。停止服务使用各自窗口的 Ctrl+C，不删除数据库。

后端健康检查：[health](http://127.0.0.1:8000/api/v1/health)；开发接口文档：[API 文档](http://127.0.0.1:8000/docs)。业务接口需要登录。

建议操作顺序：公司资料中新建公司→职位库新建岗位并粘贴 JD→人才库录入人才→人才详情追加履历/沟通→关联职位并更新推荐状态。

## 阶段 B 日常使用

- 人才库可按简历来源和建联日期筛选；职位库可按公司和招聘状态筛选，关键词同时覆盖职位/公司。点击“重置”恢复列表。
- “自定义字段”选择人才/职位，管理员可新增文本、数字、日期、单选字段并排序。字段类型固定；选项可追加/改显示名，不能移除历史选项。停用字段保留历史值，普通用户仍可录入已启用字段。
- 新字段设为必填时，历史记录不会自动填入猜测值，下次保存时需要补齐。人才和岗位编辑弹窗会自动显示启用字段，详情展示历史值。
- 任职经历、沟通时间线和公司事实资料均可逐条编辑；不提供物理删除或自动合并。
- 人才库点击“导入人才”，或侧栏进入“人才导入”；下载的 XLSX 空模板采用“候选人”工作表，第 1 行空白，第 2 行依次为日期、姓名、公司、职位、联系电话、记录、链接。已有 `.xlsx` 和 UTF-8 CSV 仍可上传，旧 `.xls` 请另存为 `.xlsx`。
- 上传后选择工作表和表头行，核对列映射；多个电话/微信/邮箱列可分别映射，含混的联系方式原文映射为“其他/原文”。支持映射扩展字段。
- 系统建议第二行表头及上述七列映射；日期支持 `YYYY.MM.DD`，空日期保持未知。“链接”保存为人才扩展信息中的“简历链接”，最长 2,000 字，保留 Excel 超链接的实际目标；详情可点击 HTTP(S) 地址，其他内容仅显示文字。空模板联系电话预设为文本，已有数字电话仍需核对前导零。
- “简历链接”是固定字段，其值可在人才编辑中维护，定义不能停用或改类型。此次兼容不改变数据库结构；旧的未提交预览首次打开后，若提示字段定义更新，重新生成预览再确认。
- 点击“生成校验预览”；左右滚动查看全部字段。错误行点击“修正内容”，重复行明确选择“仍然新建”或“跳过重复行”，数字联系方式需核对提醒。
- 全部待提交行通过后点击“确认提交导入”。只新增人才；历史沟通时间未知时保留空。刷新或网络重试同一批次不重复新增；历史批次只能由创建者查看。
- 导入初始限制：单文件 10 MB、每次最多 5,000 位、工作表不超过 10,000 行/100 列；另有 ZIP 展开及累计文字上限，超限请拆分。公式单元格需转普通值或在预览中修正，不执行公式或宏。

## 数据位置与恢复

- 数据库：`var/hunter.db`。
- 私有附件：`var/uploads/`，文件名采用随机标识，原名保存在数据库。
- 导入原件：`var/imports/`，随机标识保存；取消只改变批次状态，不自动删除文件或历史行。
- 阶段 B 升级前备份：`var/backups/stage-b-<timestamp>.db`，使用 SQLite 备份 API 并验证完整性。该自动备份只覆盖数据库，日常完整备份仍同时包含原附件和导入文件。
- 不把 `var/`、虚拟环境、构建产物和依赖目录提交到 Git。
- 备份前停止后端，然后同时复制完整 `var/` 目录到用户选定的私有位置。停止期间无新写入，数据库和附件一起备份。
- 恢复涉及覆盖/删除现有文件或数据时先确认范围；本阶段没有运行生产恢复或公开部署。

## 在新环境重建

需要满足上游 Node engines、pnpm 和 Python 3.12。先按项目目录建立本地 Python 虚拟环境，再安装固定依赖；不要全局安装。

```powershell
# 已进入 backend，且 .venv 已由可用 Python 创建
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
# 仅在授权的全新开发库执行
.\.venv\Scripts\python.exe -X utf8 -m app.cli init-db
```

```powershell
# frontend
pnpm install --frozen-lockfile --ignore-scripts --store-dir .pnpm-store --config.manage-package-manager-versions=false
```

运行时从进程环境读取 `DATABASE_URL`、`UPLOAD_ROOT`、`HUNTER_ENV`；不读取 `.env`。默认仅本地开发，Cookie 允许本地 HTTP。生产必须设置 HTTPS/Secure Cookie，并在实际 PostgreSQL 上重新验证。

已有阶段 A 默认开发库升级阶段 B：在 backend 运行 `.venv\Scripts\python.exe -X utf8 -m app.cli upgrade-db`。入口只接受已授权的 `var/hunter.db`、先创建不覆盖的备份并校验，再执行 `0001→0002_stage_b`；已在阶段 B 时不重复升级。当前工作区已完成该升级，无需重跑。服务启动不会自动迁移。

## 验证

```powershell
# backend
.\.venv\Scripts\python.exe -m ruff check app tests migrations
.\.venv\Scripts\python.exe -m pytest -q
# frontend
pnpm typecheck
pnpm lint:check
pnpm build
```

构建输出路径会打印为 `BUILD_OUTPUT=...`，旧构建不自动删除。

浏览器脚本 `frontend/scripts/smoke.mjs` 使用已安装的 Playwright。可通过 `PLAYWRIGHT_MODULE` 指向现有模块，通过 `HUNTER_BROWSER_PATH` 指向现有浏览器，不强制新安装。

脚本默认占用 8001/8850，若已被使用会拒绝启动；用独立系统临时目录数据库、随机合成账号和隐藏窗口的子进程，结束后停止这些子进程。不会修改 `var/hunter.db`，不会将密码打印或写入项目。截图在 `frontend/.artifacts/browser-<run-id>/`。

`smoke.mjs` 同时调用 `scripts/ui-check.mjs`，检查旧主题偏好迁移、桌面侧栏收缩及偏好恢复、1024/1280/1440/1920 px 页面与登录，以及 1280 × 720 较矮窗口下的编辑表单、日期/时间弹层和公司资料抽屉。还保留长文本、滚动恢复、真实空态、错误恢复及减少动画偏好检查。UI 截图与 `results.json` 放 `.artifacts/ui-<run-id>/`。截图只有合成测试资料，不再运行手机/平板专用视口。

同时调用 `scripts/stage-b-check.mjs`，用生成的合成 `.xlsx` 和 UTF-8 BOM CSV 验证字段管理、动态录入、逐条编辑、筛选、映射、公式/日期错误修正、重复处理、真实提交及桌面布局。保留七列模板、第二行表头、电话前导零及实际超链接验证；结果和截图放 `.artifacts/stage-b-<run-id>/`。后端导入依赖为 openpyxl 3.1.5、defusedxml 0.7.1、et_xmlfile 2.0.0，精确版本已入锁文件。

当前 UI 默认浅色、蓝紫主题和纵向导航；主题样式集中在 `src/style/hunter-theme.scss`，业务页面样式在 `src/views/hunter/style.scss`。首启只迁移带 `hunter-` 前缀的显示偏好，保留账号资料及无关存储；原模板设置文件仍保留，不暴露尚未适配的布局选项。

## 当前限制

- 当前数据为同一个内部工作台共享，所有登录使用者可访问；没有部门/顾问私有库隔离。
- 公司/职位/人才编辑接口当前要求完整编辑表单，前端已按该契约提交；尚不承诺任意局部字段 PATCH。
- 历史记录支持逐条编辑并保留创建/更新时间；没有完整操作审计版本回放或物理删除。
- 不提供删除接口或自动消息发送，也没有自动数据库迁移。
- PostgreSQL 驱动已准备，实际 PostgreSQL、公开部署、DeepSeek 与 OCR 均未验证。
- 登录保护和本地私有附件已经验证；公开服务上线前需另行落实登录限流、网络访问策略和部署验收。
