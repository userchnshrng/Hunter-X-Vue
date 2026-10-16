# Hunter-X-Vue 工作规范

## 项目与授权

- 面向盘晋的中文猎头内部工作台；已选择 Pure Admin 精简版作为前端底座。
- 当前阶段：阶段 A、UI 和阶段 B 已实现并完成验收，分别见对应 validation 文档。C–E 尚未实现，新增敏感操作仍按红线单独确认。
- 用户已确认 `docs/ui-redesign-plan.md`；参考图风格 UI 已验收，记录见 `docs/ui-validation.md`。后续业务页面沿用该主题。
- 用户已确认 `docs/stage-b-plan.md`：授权阶段 B 实施、新增 3 张表、隔离测试迁移，以及备份后升级本地 SQLite 开发库。C–E 尚未推进；不重复请求已授权操作。
- 已获具体授权：`docs/stage-a-review.md` 所列 10 张表的初始迁移、独立测试库和 `var/hunter.db` SQLite 开发库；不重复请求这一范围的授权。部署 PostgreSQL 尚未验证。
- 大规模实现前提交具体方案，取得用户确认；当前 skill 的创建不等于业务实现已验收。
- 默认中文沟通；代码、命令、变量和文件名使用英文。
- 用户已确认 `docs/desktop-scope-plan.md`，授权清理手机专用代码及测试。业务仅在电脑浏览器使用；后续验收覆盖桌面窗口，不再要求手机端适配或手机端测试。实施状态以方案中的实际结果为准。
- 先更新规范、再改变实践；下级规范仅在对应目录内细化本文件。

## 目录结构与命名

| 路径 | 内容与约定 |
| --- | --- |
| `AGENTS.md` | 项目级规则、目录和验证入口。 |
| `skill/skill-search-from-github/` | 用户原有的 GitHub 搜索技能文档，保留原内容和用户调整后的路径。 |
| `skill/hunter-workbench/SKILL.md` | 本项目开发技能入口，使用英文小写连字符命名。 |
| `skill/hunter-workbench/references/` | 按业务、架构、导入与 AI、实施计划、验收、来源拆分的 Markdown 规范。 |
| `skill/hunter-workbench/agents/` | 本技能的 UI 元数据；不放业务配置或凭据。 |
| `frontend/` | 方案确认后才创建，放 Pure Admin 前端；业务模块按 candidates/jobs/companies 等命名。 |
| `backend/` | 方案确认后才创建，放 FastAPI 服务、迁移和测试。 |
| `docs/` | 实施时需要的启动、运维和上游版本记录，不复制技能规范。 |
| `var/` | 实施时本地运行数据、附件与派生文件，必须忽略版本控制。 |

- 新增未列出的顶层目录前，先在本文件说明用途和命名规则。
- 临时文件放系统临时目录；测试使用虚构数据及独立临时目录，不复制真实简历到测试目录。
- 清理规则：用户文件、附件、历史 skill 和现有目录均不得自动删除；确需删除先取得用户授权。
- 不为尚未开始的阶段创建空目录、占位代码或假验证脚本。
- 前端无删除构建校验输出约定为 `frontend/.artifacts/build-<run-id>/`，忽略版本控制；不自动清理旧输出。
- `docs/stage-a-review.md` 记录本阶段数据库范围与环境选择，`docs/upstream.md` 记录模板来源，`docs/development.md` 记录实际启动方式。后端虚拟环境放 `backend/.venv/` 并忽略版本控制。
- `docs/ui-redesign-plan.md` 放 UI 改造范围、步骤和验收清单；`docs/assets/` 放用户提供且需在项目内保留的设计参考，文件采用英文小写连字符命名，不放业务附件或真实候选人资料。
- `docs/ui-validation.md` 放 UI 实际实现、验证结果、截图路径和限制；派生截图仍放前端 `.artifacts/`，文档只链接，不复制测试资料。
- `docs/stage-b-plan.md` 放阶段 B 的具体交付、接口、数据变更、依赖与验收方案；`docs/stage-b-validation.md` 仅在实际实施并产生验证结果时创建。
- 阶段 B 获确认后，导入原件拟放 `var/imports/<random-id>`，文件名使用随机标识，批次元数据保留原名与摘要；只经认证接口访问，不自动清理。合成工作簿由测试在独立临时目录生成，不放真实业务资料。
- 阶段 B 获确认后，SQLite 升级前备份拟放 `var/backups/stage-b-<timestamp>.db`；必须创建新文件并验证可读，不覆盖旧备份、不自动删除。
- `backend/app/assets/` 放不含业务数据的空白导入模板，英文小写连字符命名；目录内 `AGENTS.md` 说明生成与保留规则。真实候选人工作簿仅在用户指定原位置只读核对，不复制到项目、测试或日志。
- `docs/import-template-adaptation.md` 记录用户表格式兼容规则及验证；本次只改模板和兼容逻辑，实际人才导入由用户在预览后确认，不执行新的 schema 或数据迁移。
- `docs/desktop-scope-plan.md` 记录桌面端支持范围、手机专用代码清理清单、保留项和验收方式。既有 validation 文档保留历史事实，不因范围调整删除旧截图或改写旧验证结果。

## 自主边界

以下操作必须先取得对应授权：删除文件/目录/git 历史；修改 `.env`、密钥、token、CI/CD；数据库 schema 变更或迁移；git push/rebase/reset --hard/强推；全局安装或系统配置变更；公开发布。

- 已明确授权的同一动作不重复请求；一般开发确认不自动扩大为上述敏感动作的授权。
- 不输出密钥、密码、完整认证头或真实简历到日志、提交或示例。
- 创建和校验 skill、编写方案、只读调研可继续执行；不安装全局工具来绕过环境缺失。

## 验证

### 当前文档阶段

1. 优先运行系统 `skill-creator/scripts/quick_validate.py` 校验 `skill/hunter-workbench`；使用现有 Python 解释器，不安装全局依赖。
2. 检查所有本地引用能解析、技能 YAML 元数据可解析、无未完成的生成器占位文本。
3. 对业务场景、数据关联和权限边界做静态场景复核。明确区分文档校验与应用运行测试。

### 业务开发阶段

- 前端目录执行：`pnpm typecheck`、`pnpm lint:check`、`pnpm build`；构建使用独立目录且不自动清空旧输出。
- 后端目录执行：`.venv/Scripts/python.exe -m ruff check app tests migrations`、`.venv/Scripts/python.exe -m pytest -q`。
- 浏览器关键路径：前端目录 `node scripts/smoke.mjs`；使用已有 Playwright/浏览器，环境与隔离方式见 `docs/development.md`。
- 新的 UI 验收仅针对桌面浏览器，默认视口宽度 1024、1280、1440、1920 px；其中 1024 px 覆盖电脑窄窗口，另验 1280 × 720 的较矮窗口。手机/平板专用视口不再列为验收项，不用跳过标记掩盖残留。
- 后端固定依赖见 `backend/requirements-lock.txt`；前端使用锁文件。新增或调整后更新实际验证记录。
- 至少覆盖前端类型检查与构建、后端静态检查及关键业务测试、真实浏览器关键路径。
- 上游脚本若隐含删除、修改 `.env` 或数据迁移，不因脚本名称普通而直接执行。
- 不通过注释报错、跳过检查或虚假 mock 成功结果掩盖失败。
