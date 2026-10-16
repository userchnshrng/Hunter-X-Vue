import { createRequire } from "node:module";
import { randomBytes } from "node:crypto";
import { spawn } from "node:child_process";
import { mkdir, access } from "node:fs/promises";
import { resolve } from "node:path";
import assert from "node:assert/strict";
import {
  seedLegacyTheme,
  checkEmptyDashboard,
  checkAuthenticatedUI,
  checkLoginUI
} from "./ui-check.mjs";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const password = randomBytes(24).toString("base64url");
const testPort = Number(process.env.HUNTER_TEST_PORT || 8001);
const uiPort = Number(process.env.HUNTER_TEST_UI_PORT || 8850);
const apiTarget = `http://127.0.0.1:${testPort}`;
const base = `http://127.0.0.1:${uiPort}`;
const backend = resolve("../backend");
const children = [];
let browser;
const errors = [];
const checks = [];
async function settle(page) {
  await page.waitForFunction(() => {
    const content = document.querySelector(".hunter-page");
    return (
      content &&
      getComputedStyle(content).opacity === "1" &&
      !document.querySelector(".el-loading-mask") &&
      !document
        .getAnimations()
        .some(
          animation =>
            animation.playState === "running" &&
            animation.effect?.getComputedTiming().iterations !== Infinity
        )
    );
  });
}
async function ready(url) {
  for (let attempt = 0; attempt < 120; attempt++) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      /* A newly spawned local server may not yet listen. */
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  throw new Error(`Local test service did not start: ${url}`);
}
function start(command, args, cwd, env) {
  const child = spawn(command, args, {
    cwd,
    env: { ...process.env, ...env },
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"]
  });
  child.on("error", error => errors.push(error.message));
  child.stderr.on("data", data => {
    const text = String(data);
    if (/Traceback|Error:/.test(text)) errors.push(text.slice(0, 1000));
  });
  children.push(child);
  return child;
}
try {
  // Never attach a synthetic test to an existing service on one of these ports.
  for (const target of [apiTarget, base]) {
    let occupied = false;
    try {
      await fetch(target);
      occupied = true;
    } catch {}
    assert.equal(occupied, false, `Test port is already occupied: ${target}`);
  }
  start(
    resolve(backend, ".venv/Scripts/python.exe"),
    ["-X", "utf8", "-m", "tests.browser_server"],
    backend,
    { HUNTER_TEST_PASSWORD: password, HUNTER_TEST_PORT: String(testPort) }
  );
  await ready(`${apiTarget}/api/v1/health`);
  start(
    process.execPath,
    [
      "node_modules/vite/bin/vite.js",
      "--host",
      "127.0.0.1",
      "--port",
      String(uiPort)
    ],
    process.cwd(),
    { HUNTER_API_TARGET: apiTarget }
  );
  await ready(base);
  const browserPath = process.env.HUNTER_BROWSER_PATH;
  if (browserPath) await access(browserPath);
  browser = await chromium.launch({
    headless: true,
    ...(browserPath ? { executablePath: browserPath } : {})
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    timezoneId: "Asia/Shanghai"
  });
  const page = await context.newPage();
  await seedLegacyTheme(page);
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(base);
  await page.getByRole("heading", { name: "登录工作台" }).waitFor();
  await page.getByLabel("用户名", { exact: true }).fill("browser-test");
  await page.getByLabel("密码", { exact: true }).fill(password);
  await page.getByRole("button", { name: "进入工作台" }).click();
  await page
    .getByRole("heading", { name: "让合适的人，遇见合适的机会" })
    .waitFor();
  checks.push("real login and dashboard");
  await checkEmptyDashboard(page, settle);
  await page.goto(`${base}/companies`);
  await page.getByRole("button", { name: "新增公司", exact: true }).click();
  await page
    .getByLabel("公司名称", { exact: true })
    .fill("合成示例 · 云杉科技");
  await page.getByLabel("行业", { exact: true }).fill("企业软件");
  await page
    .getByLabel("业务简介", { exact: true })
    .fill("用于自动化验证的虚构企业，不代表真实公司现状。");
  await page.getByRole("button", { name: "保存公司", exact: true }).click();
  await page
    .getByRole("button", { name: "合成示例 · 云杉科技", exact: true })
    .waitFor();
  checks.push("company persisted through real API");
  await page.goto(`${base}/jobs`);
  await page.getByRole("button", { name: "新增职位", exact: true }).click();
  await page.getByRole("combobox", { name: "公司", exact: true }).click();
  await page
    .getByRole("option", { name: "合成示例 · 云杉科技", exact: true })
    .click();
  await page
    .getByLabel("职位名称", { exact: true })
    .fill("产品负责人 · 合成岗位");
  await page.getByLabel("汇报上级", { exact: true }).fill("业务总经理");
  await page
    .getByLabel("业务具体情况", { exact: true })
    .fill("负责虚构产品线的规划与交付。");
  await page
    .getByLabel("JD 原文", { exact: true })
    .fill("合成 JD：负责企业软件产品，具备产品规划与跨团队协作能力。");
  await page.getByRole("button", { name: "保存职位", exact: true }).click();
  await page
    .getByRole("link", { name: "产品负责人 · 合成岗位", exact: true })
    .waitFor();
  checks.push("job form saves without AI calls");
  await page.goto(`${base}/candidates`);
  await page.getByRole("button", { name: "新增人才", exact: true }).click();
  await page.getByLabel("姓名", { exact: true }).fill("林知远（合成人才）");
  await page
    .getByLabel("当前公司", { exact: true })
    .fill("合成示例 · 青禾软件");
  await page.getByLabel("当前职位", { exact: true }).fill("高级产品经理");
  await page.getByLabel("简历来源", { exact: true }).fill("自动化验证合成数据");
  await page.getByRole("button", { name: "添加联系方式", exact: true }).click();
  await page
    .getByLabel("联系方式内容", { exact: true })
    .fill("synthetic-contact");
  await page.getByRole("button", { name: "保存人才", exact: true }).click();
  await page
    .getByRole("link", { name: "林知远（合成人才）", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "林知远（合成人才）", exact: true })
    .waitFor();
  const candidateUrl = page.url();
  await page
    .getByLabel("沟通内容", { exact: true })
    .fill("合成沟通：候选人愿意了解岗位，团队规模待核实。");
  await page.getByRole("button", { name: "保存沟通记录", exact: true }).click();
  await page
    .getByText("合成沟通：候选人愿意了解岗位，团队规模待核实。", {
      exact: true
    })
    .waitFor();
  checks.push("candidate and communication persisted");
  await page.getByRole("button", { name: "编辑人才", exact: true }).click();
  await page
    .getByLabel("当前职位", { exact: true })
    .fill("产品负责人（已核实）");
  await page.getByRole("button", { name: "保存人才", exact: true }).click();
  await page
    .getByText("合成示例 · 青禾软件 · 产品负责人（已核实）", { exact: true })
    .waitFor();
  checks.push("editing reactive candidate data");
  await page.getByRole("combobox", { name: "关联职位", exact: true }).click();
  await page
    .getByRole("option", {
      name: "产品负责人 · 合成岗位 · 合成示例 · 云杉科技",
      exact: true
    })
    .click();
  await page.getByRole("button", { name: "关联职位", exact: true }).click();
  await page
    .getByRole("link", { name: "产品负责人 · 合成岗位", exact: true })
    .waitFor();
  await settle(page);
  await page
    .locator(".el-select")
    .filter({
      has: page.getByRole("combobox", { name: "推荐状态", exact: true })
    })
    .click();
  await page.getByRole("option", { name: "面试中", exact: true }).click();
  await page.getByRole("combobox", { name: "推荐状态", exact: true }).waitFor();
  await page
    .locator(".el-select")
    .filter({
      has: page.getByRole("combobox", { name: "推荐状态", exact: true })
    })
    .getByText("面试中", { exact: true })
    .waitFor();
  checks.push("linking a job and updating application status through the UI");
  await page.getByLabel("上传附件", { exact: true }).setInputFiles({
    name: "synthetic-resume.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("合成简历：产品规划与交付")
  });
  const attachment = page.getByRole("button", {
    name: "synthetic-resume.txt",
    exact: true
  });
  await attachment.waitFor();
  const downloadPromise = page.waitForEvent("download");
  await attachment.click();
  const download = await downloadPromise;
  assert.equal(download.suggestedFilename(), "synthetic-resume.txt");
  checks.push("private attachment upload and authenticated download");
  await page.reload();
  await page
    .getByText("合成沟通：候选人愿意了解岗位，团队规模待核实。", {
      exact: true
    })
    .waitFor();
  assert.equal(page.url(), candidateUrl);
  const storage = await page.evaluate(() => Object.values(localStorage));
  assert.ok(
    storage.every(
      value => !value.includes("accessToken") && !value.includes("refreshToken")
    )
  );
  const cookies = await context.cookies();
  const refresh = cookies.find(cookie => cookie.name === "hunter_refresh");
  assert.ok(refresh?.httpOnly);
  checks.push("page refresh restores session; no credentials in localStorage");
  const output = resolve(".artifacts", `browser-${Date.now()}`);
  await mkdir(output, { recursive: true });
  await page.goto(`${base}/welcome`);
  await page.getByText("合成测试账号", { exact: true }).waitFor();
  await settle(page);
  await page.screenshot({
    path: resolve(output, "dashboard.png"),
    fullPage: true
  });
  await page.goto(`${base}/candidates`);
  await page
    .getByRole("link", { name: "林知远（合成人才）", exact: true })
    .waitFor();
  await settle(page);
  await page.screenshot({
    path: resolve(output, "candidates.png"),
    fullPage: true
  });
  await checkAuthenticatedUI(page, base, candidateUrl, settle);
  await page.getByText("合成测试账号", { exact: true }).click();
  await page.getByText("退出系统", { exact: true }).click();
  await page.getByRole("heading", { name: "登录工作台" }).waitFor();
  await page.goto(`${base}/candidates`);
  await page.getByRole("heading", { name: "登录工作台" }).waitFor();
  checks.push("logout revokes refresh and blocks protected pages");
  const ui = await checkLoginUI(page);
  assert.deepEqual(errors, []);
  console.log(
    JSON.stringify({ status: "PASS", checks, screenshots: output, ui }, null, 2)
  );
} finally {
  if (browser) await browser.close();
  for (const child of children) child.kill();
}
