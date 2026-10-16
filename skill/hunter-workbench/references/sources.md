# 来源与事实边界

核查日期：2026-10-16。外部仓库、版本和 API 会变化；实施时重新读取实际内容并固定上游 commit。以下是来源归属，不表示已在本机安装或运行这些项目。

## Pure Admin

- [官方完整版](https://github.com/pure-admin/vue-pure-admin)：界面与组件方案参考，MIT；本项目保留原作者版权与许可证。
- [官方非国际化精简版](https://github.com/pure-admin/pure-admin-thin)：选定的前端来源。
- [精简版 package.json](https://github.com/pure-admin/pure-admin-thin/blob/main/package.json)：核查时版本字段为 6.2.0；依赖含 Vue 3、TypeScript、Element Plus、Pinia、Vite。Node engines 为 `^20.19.0 || >=22.13.0`，pnpm 为 `>=9`。这不是永久固定的运行要求。
- [HTTP 封装](https://github.com/pure-admin/pure-admin-thin/blob/main/src/utils/http/index.ts)：Axios、默认 10 秒超时、登录/刷新白名单、队列刷新机制；参考其请求边界，不盲目继承失败处理。
- [登录 API](https://github.com/pure-admin/pure-admin-thin/blob/main/src/api/user.ts)：模板使用 accessToken/refreshToken 等字段，本项目应集中适配。
- [路由入口](https://github.com/pure-admin/pure-admin-thin/blob/main/src/router/index.ts)：自动发现路由模块和现有导航守卫。
- [用户 store](https://github.com/pure-admin/pure-admin-thin/blob/main/src/store/modules/user.ts)：登录状态与权限路由的接合点。

本技能提炼的方法：复用后台框架、沿路由/API/store 扩展业务、把文件和 AI 放服务端、在适配边界处理模板约束。不是复制整个模板手册，也不代表模板自带猎头功能。

## DeepSeek

- [官方首次 API 调用说明](https://api-docs.deepseek.com/)：核查时提供 OpenAI 兼容的聊天接口；本项目使用后端 HTTP 客户端即可，不依赖 OpenAI 账号或其 API key。
- [官方 API 参考](https://api-docs.deepseek.com/api/create-chat-completion)：实施时核实模型、结构化输出、参数和错误格式。
- 模型名称、价格、视觉能力和联网能力均不得凭历史印象硬编码。模型负责分析已提供的材料，公司近况的采集属于独立能力。
- 本次未验证 JSON 模式指南页面的可访问内容，因此技能对 JSON 模式采用条件式建议，强制保证来自本地结构校验。

## 规范来源

- 本项目根 `AGENTS.md`：目录、验证与自主边界。
- 用户的业务描述和本次选型确认：需求事实。
- 本技能的后端、数据库、认证、任务和自定义字段方案：针对本项目的设计建议，不是 Pure Admin 的官方后端方案。
- `skill-creator`：使用精简入口与按需引用、避免占位文件、校验元数据的技能编写方法。

不把源仓库示例账号、示例密钥或开发部署参数带入实际环境。Star 数不是安全性、维护成本或业务完整性的证明。
