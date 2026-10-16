# 前端约定

- 使用 Pure Admin 官方精简版，来源 commit 和适配说明放根目录 `docs/upstream.md`。
- 沿用 `src/layout`、`src/router/modules`、`src/utils/http`、Element Plus；猎头业务页面放 `src/views/hunter/`，业务接口放 `src/api/hunter.ts`。
- 状态集中在 Pinia；认证凭据不进 localStorage。业务和认证连接真实后端，不使用 mock 运行。
- `scripts/` 放跨平台开发/无删除构建入口；构建输出到 `.artifacts/build-<run-id>/`，保留旧输出。
- `scripts/smoke.mjs` 用现有 Playwright 启动独立测试前后端，截图放 `.artifacts/browser-<run-id>/`，数据库和合成账号在系统临时目录，不使用开发库。
- `scripts/ui-check.mjs` 是 smoke 调用的 UI 验收模块，覆盖主题迁移、响应式、弹层、键盘和空态；截图及结果放 `.artifacts/ui-<run-id>/`，不得把合成资料写入开发库。
- 不创建或修改 `.env`、CI/CD；开发端口与代理通过 Vite 代码和进程环境设置。
- `pnpm typecheck`；`pnpm lint:check`；`pnpm build`。按实际脚本验证；无 `--fix` 的检查不改写文件。
- 原模板文件保留，停用示例路由和 mock，不删除目录。界面以日常中文业务术语为主。
- UI 改造前读 `../docs/ui-redesign-plan.md` 和 `../skill/hunter-workbench/references/ui-design.md`。方案已获用户确认，可连续实施并验收；B–E 暂不推进。
- 主题文件为 `src/style/hunter-theme.scss`；颜色、圆角、间距通过命名空间变量统一，业务排版放 `src/views/hunter/style.scss`，日期弹层定位共用 `src/views/hunter/ui.ts`。新验收截图放 `.artifacts/ui-<run-id>/`。
