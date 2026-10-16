# 后端约定

- FastAPI 单服务；`app/api` 是接口，`app/schemas` 是契约，`app/models` 是持久化，`app/services` 是业务规则，`app/core` 是数据库/认证/配置。
- `migrations/versions` 只放经授权的迁移，禁止启动自动 `create_all` 或迁移。`tests/` 只用合成数据与独立测试库。
- `.venv/` 是本项目依赖环境，忽略版本控制；不全局安装。不创建/修改 `.env`。
- 已授权的初始表清单见 `../docs/stage-a-review.md`；超出范围的 schema 另行确认。
- 阶段 B 的新增 3 表、备份及迁移范围已获用户确认，见 `../docs/stage-b-plan.md`。定义/导入接口和契约按 `fields.py`、`imports.py` 命名，业务规则放 services；既有表不改列，不执行删除或降级。
- UUID 用字符串表示，UTC 时间存储，JSON 数据保持 PostgreSQL 兼容；SQLite 必须启用外键。
- 密码 Argon2 摘要、随机访问/刷新凭证仅存摘要；登录不打印明文凭据。管理员通过本地 CLI 隐藏输入创建。
- 所有业务和私有文件接口认证。沟通与推荐必须属于同一人才；重复推荐保持幂等。
- 验证：`.venv/Scripts/python.exe -m ruff check app tests migrations` 与 `.venv/Scripts/python.exe -m pytest -q`。
- `app/assets/` 只放已去除真实记录的空模板；保留列顺序、工作表名与表头位置。候选人链接复用 JSON 附加值中的固定 `resume_link`，不增加数据库列，不自动导入实际记录。
