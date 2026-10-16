# 本地使用与开发

## 当前能力

阶段 A 提供真实登录、公司及来源资料、职位、人才、履历追加、沟通追加、职位推荐状态、私有附件上传下载。使用本地 SQLite，重启不丢数据。

Excel 导入、自定义字段管理、PDF/Word/OCR 文字提取、DeepSeek 匹配和话术尚未接入，属于后续阶段。现在上传附件只保存原件，不会解析或调用 AI。

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

## 数据位置与恢复

- 数据库：`var/hunter.db`。
- 私有附件：`var/uploads/`，文件名采用随机标识，原名保存在数据库。
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

`smoke.mjs` 同时调用 `scripts/ui-check.mjs`，检查旧主题偏好迁移、侧栏/手机抽屉、1440/1280/1024/768/390/360 px 页面、编辑表单及弹层、长文本、真实空态、错误恢复和登录适配。UI 截图与 `results.json` 放 `.artifacts/ui-<run-id>/`。截图只有合成测试资料。

当前 UI 默认浅色、蓝紫主题和纵向导航；主题样式集中在 `src/style/hunter-theme.scss`，业务页面样式在 `src/views/hunter/style.scss`。首启只迁移带 `hunter-` 前缀的显示偏好，保留账号资料及无关存储；原模板设置文件仍保留，不暴露尚未适配的布局选项。

## 当前限制

- 当前数据为同一个内部工作台共享，所有登录使用者可访问；没有部门/顾问私有库隔离。
- 公司/职位/人才编辑接口当前要求完整编辑表单，前端已按该契约提交；尚不承诺任意局部字段 PATCH。
- 目前主要支持追加履历和沟通记录；这些历史记录的独立编辑属于后续维护完善。
- 不提供删除接口或自动消息发送，也没有自动数据库迁移。
- PostgreSQL 驱动已准备，实际 PostgreSQL、公开部署、DeepSeek 与 OCR 均未验证。
- 登录保护和本地私有附件已经验证；公开服务上线前需另行落实登录限流、网络访问策略和部署验收。
