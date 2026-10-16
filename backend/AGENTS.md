# 后端约定

- FastAPI 单服务；`app/api` 是接口，`app/schemas` 是契约，`app/models` 是持久化，`app/services` 是业务规则，`app/core` 是数据库/认证/配置。
- `migrations/versions` 只放经授权的迁移，禁止启动自动 `create_all` 或迁移。`tests/` 只用合成数据与独立测试库。
- `.venv/` 是本项目依赖环境，忽略版本控制；不全局安装。不创建/修改 `.env`。
- 已授权的初始表清单见 `../docs/stage-a-review.md`；超出范围的 schema 另行确认。
- UUID 用字符串表示，UTC 时间存储，JSON 数据保持 PostgreSQL 兼容；SQLite 必须启用外键。
- 密码 Argon2 摘要、随机访问/刷新凭证仅存摘要；登录不打印明文凭据。管理员通过本地 CLI 隐藏输入创建。
- 所有业务和私有文件接口认证。沟通与推荐必须属于同一人才；重复推荐保持幂等。
- 验证：`.venv/Scripts/python.exe -m ruff check app tests migrations` 与 `.venv/Scripts/python.exe -m pytest -q`。
