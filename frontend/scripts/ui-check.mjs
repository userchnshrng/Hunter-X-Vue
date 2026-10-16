import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

export const uiOutput = resolve(".artifacts", `ui-${Date.now()}`);
const results = [];
const fonts = {};
async function animationsFinished(page) {
  await page.waitForFunction(
    () =>
      !document
        .getAnimations()
        .some(
          animation =>
            animation.playState === "running" &&
            animation.effect?.getComputedTiming().iterations !== Infinity
        )
  );
}
async function screenshot(page, name) {
  await animationsFinished(page);
  await mkdir(uiOutput, { recursive: true });
  await page.screenshot({
    path: resolve(uiOutput, `${name}.png`),
    fullPage: true
  });
}
async function noOverflow(
  page,
  label,
  selectors = ["html", "body", ".hunter-content"]
) {
  const dimensions = await page.evaluate(
    selectors =>
      selectors.flatMap(selector =>
        [...document.querySelectorAll(selector)].map(el => ({
          selector,
          client: el.clientWidth,
          scroll: el.scrollWidth
        }))
      ),
    selectors
  );
  for (const item of dimensions)
    assert.ok(
      item.scroll <= item.client + 1,
      `${label}: ${JSON.stringify(item)}`
    );
}
async function insideViewport(locator, page, label) {
  await locator.waitFor({ state: "visible" });
  await animationsFinished(page);
  const box = await locator.boundingBox();
  const viewport = page.viewportSize();
  assert.ok(
    box &&
      box.x >= -1 &&
      box.y >= -1 &&
      box.x + box.width <= viewport.width + 1 &&
      box.y + box.height <= viewport.height + 1,
    `${label}: ${JSON.stringify(box)}`
  );
}
export async function seedLegacyTheme(page) {
  await page.addInitScript(() => {
    if (localStorage.getItem("hunter-ui-version")) return;
    localStorage.setItem(
      "hunter-layout",
      JSON.stringify({
        layout: "horizontal",
        theme: "auroraGreen",
        epThemeColor: "#256c60",
        darkMode: true,
        sidebarStatus: true,
        overallStyle: "dark",
        themeColor: "auroraGreen"
      })
    );
    localStorage.setItem(
      "hunter-configure",
      JSON.stringify({
        hideTabs: false,
        showLogo: true,
        showModel: "smart",
        stretch: false,
        multiTagsCache: false
      })
    );
    localStorage.setItem("hunter-ui-test-unrelated", "preserved");
  });
}
export async function checkEmptyDashboard(page, settle) {
  await settle(page);
  const preferences = await page.evaluate(() => ({
    layout: JSON.parse(localStorage.getItem("hunter-layout")),
    marker: localStorage.getItem("hunter-ui-test-unrelated")
  }));
  assert.equal(preferences.layout.layout, "vertical");
  assert.equal(preferences.layout.epThemeColor, "#4f46f5");
  assert.equal(preferences.layout.darkMode, false);
  assert.equal(preferences.marker, "preserved");
  assert.equal(
    await page.getByText("从第一位人才开始", { exact: true }).count(),
    1
  );
  assert.equal(
    await page.getByText("新的机会，等你开启", { exact: true }).count(),
    1
  );
  assert.deepEqual(await page.locator(".stat-card strong").allTextContents(), [
    "0",
    "0",
    "0",
    "0"
  ]);
  await screenshot(page, "dashboard-empty-desktop");
  results.push(
    "legacy theme migrated without clearing unrelated storage; honest empty dashboard"
  );
}
export async function checkAuthenticatedUI(page, base, candidateUrl, settle) {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/welcome`);
  await settle(page);
  const jobPath = await page
    .locator(".position-row")
    .first()
    .getAttribute("href");
  // Keep a record of actual browser-computed font information for visual review.
  Object.assign(
    fonts,
    await page.evaluate(() => ({
      body: getComputedStyle(document.body).fontFamily,
      heading: getComputedStyle(document.querySelector("h1")).fontFamily
    }))
  );
  const session = await page.context().newCDPSession(page);
  await session.send("DOM.enable");
  await session.send("CSS.enable");
  const { root } = await session.send("DOM.getDocument");
  const { nodeId } = await session.send("DOM.querySelector", {
    nodeId: root.nodeId,
    selector: "h1"
  });
  fonts.rendered = (
    await session.send("CSS.getPlatformFontsForNode", { nodeId })
  ).fonts;
  await session.detach();
  await writeFile(
    resolve(uiOutput, "fonts.json"),
    JSON.stringify(fonts, null, 2)
  );

  const collapse = page.getByRole("button", { name: "收起侧栏", exact: true });
  await collapse.focus();
  await page.keyboard.press("Enter");
  await page.getByRole("button", { name: "展开侧栏", exact: true }).waitFor();
  assert.ok(
    await page.evaluate(
      () => document.activeElement?.getAttribute("aria-label") === "展开侧栏"
    )
  );
  await page.reload();
  await settle(page);
  await page.getByRole("button", { name: "展开侧栏", exact: true }).click();
  await page.getByRole("button", { name: "收起侧栏", exact: true }).waitFor();
  results.push(
    "keyboard sidebar collapse, focus retention and display preference restored after reload"
  );
  await page.setViewportSize({ width: 1024, height: 1000 });
  await page.getByRole("button", { name: "展开侧栏", exact: true }).waitFor();
  await page
    .getByRole("complementary", { name: "主导航", exact: true })
    .waitFor();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole("button", { name: "收起侧栏", exact: true }).waitFor();
  await page.getByRole("button", { name: "收起侧栏", exact: true }).click();
  await page.setViewportSize({ width: 1024, height: 1000 });
  await settle(page);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await settle(page);
  await page.getByRole("button", { name: "展开侧栏", exact: true }).click();
  results.push(
    "desktop window resizing keeps navigation available and preserves manual sidebar collapse"
  );

  // Duplicate names and long company/title/contact text use the existing UI in the isolated test database.
  await page.goto(`${base}/candidates`);
  const longName = "陈知行（同名合成人才）";
  for (let i = 0; i < 2; i++) {
    await page.getByRole("button", { name: "新增人才", exact: true }).click();
    await page.getByLabel("姓名", { exact: true }).fill(longName);
    await page
      .getByLabel("当前公司", { exact: true })
      .fill("合成示例 · " + "超长企业软件及数字化业务集团".repeat(5));
    await page
      .getByLabel("当前职位", { exact: true })
      .fill("企业级软件产品及跨部门业务协同负责人".repeat(3));
    await page
      .getByRole("button", { name: "添加联系方式", exact: true })
      .click();
    await page
      .getByRole("button", { name: "添加联系方式", exact: true })
      .click();
    await page
      .getByLabel("联系方式内容", { exact: true })
      .nth(0)
      .fill("synthetic-contact-".repeat(6));
    await page
      .getByLabel("联系方式内容", { exact: true })
      .nth(1)
      .fill("another-synthetic-contact@example.invalid");
    await page.getByRole("button", { name: "保存人才", exact: true }).click();
    await page
      .getByRole("dialog", { name: "新增人才", exact: true })
      .waitFor({ state: "hidden" });
    await settle(page);
  }
  assert.equal(
    await page.getByRole("link", { name: longName, exact: true }).count(),
    2
  );
  const longCandidatePath = await page
    .getByRole("link", { name: longName, exact: true })
    .first()
    .getAttribute("href");
  results.push(
    "duplicate names remain separate; long Chinese fields and multiple contacts rendered"
  );

  for (const width of [1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const path of [
      "/welcome",
      "/candidates",
      "/jobs",
      "/companies",
      candidateUrl.replace(base, ""),
      jobPath
    ]) {
      await page.goto(`${base}${path}`);
      await settle(page);
      await noOverflow(page, `${width}${path}`);
      if (
        path === "/welcome" ||
        path === "/candidates" ||
        (width === 1440 && path.includes("/candidates/"))
      )
        await screenshot(
          page,
          `${path === "/welcome" ? "dashboard" : path === "/candidates" ? "candidates" : "candidate-detail"}-${width}`
        );
    }
    results.push(
      `${width}px: dashboard, talent, jobs, companies and both detail pages have no page overflow`
    );
    console.log(`UI viewport ${width}px: PASS`);
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}${longCandidatePath}`);
  await settle(page);
  await noOverflow(page, "desktop long candidate detail");
  await page
    .locator(".hunter-content")
    .evaluate(el => el.scrollTo(0, el.scrollHeight));
  await page.getByRole("button", { name: "← 返回人才库", exact: true }).click();
  await page.getByRole("heading", { name: "人才库", exact: true }).waitFor();
  assert.equal(
    await page.locator(".hunter-content").evaluate(el => el.scrollTop),
    0
  );
  results.push(
    "long talent detail fits desktop; client navigation resets the content scroll position"
  );

  // Desktop windows can be short; keep dialogs, pickers and actions reachable.
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto(`${base}/jobs`);
  await settle(page);
  await page.getByRole("button", { name: "新增职位", exact: true }).click();
  let dialog = page.getByRole("dialog", { name: "新增职位", exact: true });
  await insideViewport(
    page.locator(".el-dialog:visible"),
    page,
    "short desktop job dialog"
  );
  await noOverflow(page, "short desktop job dialog", [".el-dialog"]);
  await page.getByRole("combobox", { name: "公司", exact: true }).click();
  const companyOption = page.getByRole("option", {
    name: "合成示例 · 云杉科技",
    exact: true
  });
  await companyOption.waitFor();
  await insideViewport(
    page.locator(".el-select__popper:visible").first(),
    page,
    "company dropdown"
  );
  await companyOption.click();
  await screenshot(page, "job-editor-1280x720");
  await page.getByRole("button", { name: "取消", exact: true }).click();
  await dialog.waitFor({ state: "hidden" });

  await page.goto(`${base}/candidates`);
  await settle(page);
  await page.getByRole("button", { name: "新增人才", exact: true }).click();
  dialog = page.getByRole("dialog", { name: "新增人才", exact: true });
  await page.getByRole("button", { name: "添加联系方式", exact: true }).click();
  await page
    .getByLabel("联系方式内容", { exact: true })
    .fill("synthetic-phone");
  await noOverflow(page, "short desktop candidate form", [".el-dialog"]);
  await page.getByPlaceholder("尚未建联可留空", { exact: true }).click();
  await page.locator(".el-date-picker:visible").waitFor();
  await insideViewport(
    page.locator(".el-picker__popper:visible"),
    page,
    "date picker"
  );
  await screenshot(page, "candidate-editor-date-1280x720");
  await page.keyboard.press("Escape");
  // Escape belongs to the date picker, not to the underlying dialog.
  if (await dialog.isVisible()) {
    await page.getByRole("button", { name: "取消", exact: true }).click();
    await dialog.waitFor({ state: "hidden" });
  }
  await page.goto(candidateUrl);
  await settle(page);
  await page.getByPlaceholder("未知可留空", { exact: true }).click();
  await page.locator(".el-date-picker:visible").waitFor();
  await insideViewport(
    page.locator(".el-picker__popper:visible"),
    page,
    "datetime picker"
  );
  await insideViewport(
    page
      .locator(".el-picker__popper:visible")
      .getByRole("button", { name: "确定", exact: true }),
    page,
    "datetime confirmation button"
  );
  await screenshot(page, "datetime-picker-1280x720");
  await page.keyboard.press("Escape");

  await page.goto(`${base}/companies`);
  await settle(page);
  await page
    .getByRole("button", { name: "合成示例 · 云杉科技", exact: true })
    .click();
  await page.getByRole("button", { name: "记录资料", exact: true }).waitFor();
  await insideViewport(
    page.locator(".el-drawer:visible"),
    page,
    "company drawer"
  );
  await noOverflow(page, "short desktop company facts drawer", [
    ".el-drawer__body"
  ]);
  await screenshot(page, "company-detail-1280x720");
  await page.keyboard.press("Escape");
  await page.locator(".el-drawer:visible").waitFor({ state: "hidden" });
  results.push(
    "1280x720 desktop job/talent editors, contact rows, select/date/datetime popovers and company drawer fit viewport"
  );

  await page.route("**/api/v1/dashboard", route =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "合成服务暂不可用" })
    })
  );
  await page.goto(`${base}/welcome`);
  await settle(page);
  await page.getByRole("alert").waitFor();
  assert.equal(await page.locator(".stat-card").count(), 0);
  await screenshot(page, "dashboard-error-1280x720");
  await page.unroute("**/api/v1/dashboard");
  await page.getByRole("button", { name: "刷新数据", exact: true }).click();
  await page.locator(".stat-card").first().waitFor();
  await settle(page);
  results.push(
    "visible API error with refresh recovery; no fabricated counts on failed initial load"
  );
  let release;
  const gate = new Promise(resolve => {
    release = resolve;
  });
  await page.route("**/api/v1/dashboard", async route => {
    await gate;
    await route.continue();
  });
  await page.getByRole("button", { name: "刷新数据", exact: true }).click();
  await page.locator(".el-loading-mask").waitFor();
  release();
  await settle(page);
  await page.unroute("**/api/v1/dashboard");
  results.push(
    "loading mask is visible during a pending request and clears after completion"
  );
  await page.emulateMedia({ reducedMotion: "reduce" });
  const duration = await page
    .locator(".stat-card")
    .first()
    .evaluate(el => getComputedStyle(el).transitionDuration);
  assert.ok(duration.split(",").every(value => parseFloat(value) <= 0.001));
  await page.emulateMedia({ reducedMotion: "no-preference" });
  results.push("reduced motion preference applied");
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/welcome`);
  await settle(page);
  await screenshot(page, "dashboard-desktop");
  await page.goto(`${base}/candidates`);
  await settle(page);
  await screenshot(page, "candidates-desktop");
}
export async function checkLoginUI(page) {
  for (const width of [1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 1000 });
    await noOverflow(page, `${width}px login`, [
      "html",
      "body",
      ".hunter-login"
    ]);
    await insideViewport(
      page.getByRole("button", { name: "进入工作台", exact: true }),
      page,
      "login submit"
    );
    await screenshot(page, `login-${width}`);
  }
  results.push(
    "login fits desktop window widths; zoom allowed by viewport meta"
  );
  assert.ok(
    !(
      await page.locator('meta[name="viewport"]').getAttribute("content")
    ).includes("user-scalable=0")
  );
  await mkdir(uiOutput, { recursive: true });
  await writeFile(
    resolve(uiOutput, "results.json"),
    JSON.stringify({ status: "PASS", results, fonts }, null, 2)
  );
  return { screenshots: uiOutput, checks: results.length };
}
