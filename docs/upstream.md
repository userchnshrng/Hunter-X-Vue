# Pure Admin 来源与适配

- 来源：[pure-admin/pure-admin-thin](https://github.com/pure-admin/pure-admin-thin)。
- 固定 commit：`f0ff132561ab684bb78379239adf29f9a38ac7f1`（2026-10-16 读取 main 后下载该 commit）。
- 原始版本字段：6.2.0，MIT。许可证保留在 `frontend/LICENSE`。
- 导入方式：读取该 commit 的 GitHub 源码归档，复制 202 个文件；不导入 `.env*`、`.github`、`.husky` 或 `.git`。

## 业务适配

- 保留 Pure Admin 布局、主题、标签、Element Plus、静态路由组织、请求封装入口和 Pinia。
- 新业务放 `src/views/hunter/` 与 `src/api/hunter.ts`。
- 新登录页面连接 FastAPI；访问令牌仅在内存，刷新凭据由后端 HttpOnly Cookie 管理；localStorage 只保留非敏感显示资料与布局偏好。
- 修复请求队列失败可能悬挂的问题，统一会话刷新 Promise 与业务错误。退出先完成后端撤销。
- 真实业务停用 mock 插件、演示通知和演示登录路由。原文件保留；动态视图扫描限制为实际业务与错误页面。
- 导航默认显示工作台和猎头业务；错误页保留为异常处理入口，不作为业务菜单。
- 不导入环境文件。Vite 在代码中设置本地代理、路由模式和资源根路径；开发默认只监听 127.0.0.1。

## 已解决的模板兼容问题

- 上游 CDN 插件在 import 时即读取 `vue-demi`。改为工厂函数，仅真正启用 CDN 时创建；当前正常构建使用本地打包资源。
- 源码直接使用 `tippy.js` 样式，但原 manifest 未将其声明为直接依赖。已显式加入 `tippy.js@6.3.7` 并更新锁文件，不依赖隐式提升。
- 原 build 删除 dist，且 Vite 默认可能清空输出。现通过 Node 跨平台入口构建到独立 `.artifacts/build-<run-id>/`，`emptyOutDir:false`。
- 移除 package scripts 中依赖 shell 的环境赋值、隐式清理及安装 hook；依赖安装使用 `--ignore-scripts`，不配置 Git hooks。
- 原路由滚动 Promise 在部分路径未 resolve；已补全，并添加未匹配路径的 404 处理。

## 已知工具提示

- 当前 pnpm 11 会提示忽略原 manifest 的部分旧 pnpm 字段。安装使用明确的项目 store 与 `--ignore-scripts`；未通过关闭校验解决提示。
- 原模板 Browserslist/Baseline 数据较旧；构建有更新提示，当前构建通过，尚未为消除提示升级整套依赖。
- 后端在 Windows Python 3.12 验证，实际依赖固定于 `backend/requirements-lock.txt`。

后续更新不要直接覆盖业务目录；先比较上游与本地边界改动，保留用户数据并跑阶段 A 的验证。
