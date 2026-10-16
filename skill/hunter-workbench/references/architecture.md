# 架构与工程约定

## 建议架构

这份设计需要随实施计划确认；不表示数据库或配置已经创建。

| 层 | 建议选择 | 原因与约束 |
| --- | --- | --- |
| 前端 | Pure Admin 官方非国际化精简版，Vue 3 + TypeScript + Element Plus + Pinia + Vite | 复用成熟布局与表单，中文内部系统无需先加多语言 |
| 后端 | Python FastAPI + Pydantic，SQLAlchemy 2 + Alembic | 文件处理和 DeepSeek 集中在服务端，结构化校验和迁移可审阅 |
| 数据库 | 本地 SQLite，部署 PostgreSQL | 用户因当前无 PostgreSQL/Docker 环境已确认先用 SQLite；SQLAlchemy 保持兼容，部署前验证 PostgreSQL，不能把 SQLite 测试当作 PostgreSQL 验证 |
| 附件 | 本地受控目录起步，封装存储接口 | 文件与数据库元数据分开，方便以后替换对象存储 |
| 任务 | 数据库任务记录 + 同一后端中的有限并发执行器 | 无需先加 Redis；启动时识别中断任务，禁止只存在于内存 |
| API 调用 | 后端 HTTP 客户端调用 DeepSeek | 不为兼容接口额外引入完整 AI 编排框架 |

先使用单体模块化后端。没有实测必要，不引入微服务、向量数据库、爬虫、复杂多租户或工作流引擎。

## 代码归属

实施时按根 `AGENTS.md` 创建：

```text
frontend/
  src/api/                  # candidates.ts / jobs.ts 等业务 API
  src/views/                # candidates / jobs / companies / imports / settings
  src/router/modules/       # 独立业务路由
  src/components/           # 有复用价值的上传、时间线、匹配结果组件
backend/
  app/api/                  # HTTP 路由和输入输出
  app/models/               # 持久化实体
  app/schemas/              # Pydantic 契约
  app/services/             # candidates / imports / matching 等业务用例
  app/integrations/          # deepseek / documents / ocr / storage
  app/core/                 # 配置读取、认证和数据库连接
  migrations/               # 经授权的 Alembic 迁移
  tests/                    # 合成数据、业务集成和接口测试
docs/                       # 实际启动、版本、运维记录
var/                        # 忽略版本控制的运行数据
```

这是职责边界，不要求把每个简单函数拆成独立文件。前端沿用模板已有路径，不另起重复的 HTTP 和路由体系。

## 上游适配

- 来源采用 `pure-admin/pure-admin-thin`；落地前记录具体 commit、许可证和依赖锁文件。
- 先检查 manifest、路由自动发现、HTTP 拦截器、登录和 store，再迁入业务页面。
- 当前核查发现模板 HTTP 默认超时为 10 秒；上传/长任务采用任务 ID 与状态查询，不简单把全部请求超时调成几分钟。
- 模板登录和刷新接口的 camelCase 字段需要在 API 层映射，不让全部后端业务字段被模板结构绑死。
- 认证错误必须让请求结束并跳转/提示；检查刷新失败、并发刷新和未登录请求是否会永久等待。
- mock 仅用于标识清楚的演示/测试。真实业务模式关闭假登录、假保存和假成功响应。
- 保留上游代码与版权，业务代码独立；用户禁止删除时不通过移除示例目录“瘦身”。
- 构建校验要检查显式和隐式清理：除上游 `rimraf dist` 外，Vite 也可能自动清空输出目录。无删除授权时使用新的 `.artifacts/build-<run-id>/` 并显式设置 `--emptyOutDir false`，不复用有用户文件的目录。

## 接口契约

- 业务前缀 `/api/v1`，JSON 采用 snake_case；前端模板特有字段在适配层转换。
- 列表响应建议 `{items, total, page, page_size}`，分页与过滤在服务端执行。
- 错误建议 `{code, message, details, request_id}`；保留 401/403/404/409/422/429/5xx 的实际 HTTP 含义。
- `GET /candidates` 支持姓名/公司/职位关键字、来源与建联日期过滤；POST/PATCH 分开验证。
- `GET/POST /jobs`、`GET/PATCH /jobs/{id}`；公司、经历、沟通记录和推荐使用对应资源端点。
- 文件和分析创建后返回 ID；状态可查询。上传成功与解析成功是不同状态。
- `POST /imports/preview` 建立导入预览，`POST /imports/{id}/commit` 使用确认过的映射和幂等键提交。
- `POST /applications/{id}/analyses` 创建匹配任务；话术生成使用独立任务类型和结果契约。
- 首版不提供公开候选人申请入口。以上接口名是建议，落地以生成的 OpenAPI 和前端适配为准。

## 认证与数据访问

- 首版账号由管理员建立，不开放公共注册；密码使用可靠哈希，不保留模板演示账号。
- 建议短期 access token 仅放内存，refresh token 通过 HttpOnly Cookie 传递；服务端保存可撤销的刷新凭证摘要。
- 刷新凭证轮换，退出撤销；Cookie/SameSite/CORS/CSRF 策略与实际同源或跨源部署一起确定。
- 本地仅在明确的开发环境允许非 Secure Cookie；部署环境使用 HTTPS。
- 前端菜单可见性只是体验，所有业务接口和文件下载由后端认证与授权。
- 默认管理员/普通使用者的基本权限；不提前承诺候选人私有库、复杂部门隔离和外部客户访问。

## 数据与任务一致性

- 关键外键：Employment→Candidate/Company，Job→Company，Application→Candidate/Job，Communication→Candidate/Application。
- Application 约束同一 candidate/job 不重复；分析与话术引用 Application，并保存输入版本。
- 批次提交先校验，再在事务内写入；失败回滚，保持可重试。
- 后台任务持久化 queued/running/succeeded/failed 状态、错误摘要和输入快照。
- 第一版单进程有限并发；不能随意加多个 worker 造成任务重复。需要多实例时先设计数据库领取锁和幂等机制。
- 重启时 running 任务转为可识别的中断失败，不盲目自动重复收费调用。
- 文件保存、数据库引用与失败后的孤立文件应可追踪；清理遵守用户删除授权，不偷偷清理。

## 配置和可维护性

- 方案中的配置项为 `DATABASE_URL`、`DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL`、`UPLOAD_ROOT`、`AUTH_SECRET`。
- 本文只列配置名称；不创建/修改 `.env`，不写真实值。具体配置方式在实施时展示后取得对应授权。
- 类型、业务校验和错误转换放在边界；不要在多个 Vue 组件复制同一业务规则。
- 实际版本按上游 manifest 与兼容性锁定，不把“最新”当作无限升级指令。
- 新依赖限项目内环境；锁文件可审阅。Python 用已有解释器创建项目虚拟环境，Node 使用上游支持的包管理器。
