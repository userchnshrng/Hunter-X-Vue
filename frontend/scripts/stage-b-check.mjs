import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

export async function checkStageB(page, base, candidateUrl, settle) {
  const output = resolve(".artifacts", `stage-b-${Date.now()}`);
  await mkdir(output, { recursive: true });
  const checks = [];
  async function shot(name) {
    await settle(page);
    await page.screenshot({
      path: resolve(output, `${name}.png`),
      fullPage: true
    });
  }
  async function select(name, option) {
    const combobox = page.getByRole("combobox", { name, exact: true });
    await page
      .locator(".el-select")
      .filter({ has: page.getByRole("combobox", { name, exact: true }) })
      .click();
    const dropdown = await combobox.getAttribute("aria-controls");
    assert.ok(dropdown, `Missing dropdown for ${name}`);
    await page
      .locator(`#${dropdown}`)
      .getByRole("option", { name: option, exact: true })
      .click();
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/custom-fields`);
  for (const [label, kind] of [
    ["期望地点", "文本"],
    ["期望年薪", "数字"],
    ["到岗日期", "日期"],
    ["意向状态", "单选"]
  ]) {
    await page.getByRole("button", { name: "新增字段", exact: true }).click();
    await page.getByLabel("字段名称", { exact: true }).fill(label);
    await select("字段类型", kind);
    if (kind === "单选") {
      await page.getByRole("button", { name: "添加选项", exact: true }).click();
      await page.getByLabel("选项名称", { exact: true }).fill("可沟通");
    }
    await page.getByRole("button", { name: "保存字段", exact: true }).click();
    await page
      .getByRole("dialog", { name: "新增字段", exact: true })
      .waitFor({ state: "hidden" });
    await page.getByRole("cell", { name: label, exact: true }).waitFor();
  }
  await shot("custom-fields-desktop");
  checks.push("four custom field types created through real UI");

  await page.goto(candidateUrl);
  await page.getByRole("button", { name: "编辑人才", exact: true }).click();
  await page.getByLabel("期望地点", { exact: true }).fill("杭州");
  await page.getByLabel("期望年薪", { exact: true }).fill("55");
  await page.getByLabel("到岗日期", { exact: true }).fill("2026-12-01");
  await page.getByLabel("到岗日期", { exact: true }).press("Tab");
  await select("意向状态", "可沟通");
  await page.getByRole("button", { name: "保存人才", exact: true }).click();
  await page
    .getByRole("dialog", { name: "编辑人才", exact: true })
    .waitFor({ state: "hidden" });
  await page
    .locator(".custom-value")
    .filter({ hasText: "期望年薪" })
    .getByText("55", { exact: true })
    .waitFor();
  await page.getByRole("button", { name: "编辑沟通", exact: true }).click();
  await page
    .getByLabel("编辑沟通内容", { exact: true })
    .fill("合成阶段B：已核实岗位意向。");
  await page.getByRole("button", { name: "保存修改", exact: true }).click();
  await page
    .getByText("合成阶段B：已核实岗位意向。", { exact: true })
    .waitFor();
  await page.getByText("添加任职经历", { exact: true }).click();
  await page.getByLabel("任职公司", { exact: true }).fill("合成经历公司");
  await page.getByLabel("任职职位", { exact: true }).fill("产品经理");
  await page.getByRole("button", { name: "保存经历", exact: true }).click();
  await page.getByRole("button", { name: "编辑经历", exact: true }).click();
  await page.getByLabel("编辑任职职位", { exact: true }).fill("高级产品经理");
  await page.getByRole("button", { name: "保存修改", exact: true }).click();
  await page
    .getByText("合成经历公司 · 高级产品经理", { exact: true })
    .waitFor();
  checks.push(
    "dynamic talent values, single communication and employment edits persisted"
  );

  await page.goto(`${base}/companies`);
  await page
    .getByRole("button", { name: "合成示例 · 云杉科技", exact: true })
    .click();
  await page.getByLabel("资料内容", { exact: true }).fill("合成公司事实。");
  await page.getByLabel("来源说明", { exact: true }).fill("合成公告");
  await page.getByRole("button", { name: "记录资料", exact: true }).click();
  await page.getByRole("button", { name: "编辑资料", exact: true }).click();
  await page
    .getByLabel("编辑资料内容", { exact: true })
    .fill("合成公司事实，已更新。");
  await page.getByRole("button", { name: "保存修改", exact: true }).click();
  await page.getByText("合成公司事实，已更新。", { exact: true }).waitFor();
  checks.push("company fact edited while retaining separate source fields");

  await page.goto(`${base}/imports`);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "下载导入模板", exact: true }).click();
  assert.equal(
    (await downloadPromise).suggestedFilename(),
    "人才导入模板.xlsx"
  );
  const workbook = execFileSync(
    resolve("../backend/.venv/Scripts/python.exe"),
    ["-X", "utf8", "-m", "tests.stage_b_workbook"],
    { cwd: resolve("../backend"), windowsHide: true }
  );
  await page.getByLabel("上传人才表格", { exact: true }).setInputFiles({
    name: "synthetic-stage-b.xlsx",
    mimeType:
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    buffer: workbook
  });
  await page.getByRole("combobox", { name: "工作表", exact: true }).waitFor();
  await select("工作表", "人才数据");
  const header = page.getByRole("spinbutton", {
    name: "表头所在行",
    exact: true
  });
  await header.fill("2");
  await header.press("Tab");
  await select("第5列对应字段", "联系方式 · 电话");
  await select("第6列对应字段", "联系方式 · 微信");
  await page.getByRole("button", { name: "生成校验预览", exact: true }).click();
  await page
    .locator(".import-counts")
    .getByText("错误 1", { exact: true })
    .waitFor();
  assert.equal(
    await page
      .getByRole("button", { name: "确认提交导入", exact: true })
      .isEnabled(),
    false
  );
  const importUrl = page.url();
  await shot("import-validation-desktop");
  const errorReport = page.waitForEvent("download");
  await page.getByRole("button", { name: "下载校验报告", exact: true }).click();
  assert.equal((await errorReport).suggestedFilename(), "导入校验报告.csv");
  checks.push(
    "XLSX worksheet/header selection, duplicate headers, field mapping and row-level errors"
  );

  const badRow = page
    .locator(".el-table__body tr")
    .filter({ has: page.getByRole("cell", { name: "4", exact: true }) });
  await badRow.getByRole("button", { name: "修正内容", exact: true }).click();
  await page.getByLabel("修正第1列", { exact: true }).fill("2026-10-15");
  await page.getByLabel("修正第2列", { exact: true }).fill("合成导入 · 陈明");
  await page.getByLabel("修正第5列", { exact: true }).fill("0012345");
  await page
    .getByRole("button", { name: "保存并重新校验", exact: true })
    .click();
  await page
    .getByRole("dialog", { name: "修正第 4 行", exact: true })
    .waitFor({ state: "hidden" });
  await select("第5行重复处理", "跳过重复行");
  await page
    .getByRole("button", { name: "确认提交导入", exact: true })
    .waitFor();
  await settle(page);
  assert.ok(
    await page
      .getByRole("button", { name: "确认提交导入", exact: true })
      .isEnabled()
  );
  await page.getByRole("button", { name: "确认提交导入", exact: true }).click();
  await page
    .getByText("此批次已完成：新增 2 位，跳过 1 行。重复提交不会重复建档。", {
      exact: true
    })
    .waitFor();
  await page.reload();
  await page
    .getByText("此批次已完成：新增 2 位，跳过 1 行。重复提交不会重复建档。", {
      exact: true
    })
    .waitFor();
  await shot("import-result-desktop");
  await page
    .getByRole("link", { name: "合成导入 · 许知远", exact: true })
    .click();
  await page
    .getByText("导入的历史沟通，实际沟通时间未知", { exact: true })
    .waitFor();
  await page.getByText("时间未记录", { exact: true }).waitFor();
  await page
    .locator(".custom-value")
    .filter({ hasText: "期望地点" })
    .getByText("杭州", { exact: true })
    .waitFor();
  checks.push(
    "corrected rows and explicit duplicate skip committed; import survives refresh with valid custom values"
  );

  await page.goto(`${base}/candidates`);
  await select("简历来源筛选", "合成Excel");
  await page.getByRole("button", { name: "搜索", exact: true }).click();
  await page.getByText("共 2 位人才", { exact: true }).waitFor();
  await page.getByRole("button", { name: "重置", exact: true }).click();
  await page
    .getByRole("link", { name: "林知远（合成人才）", exact: true })
    .waitFor();
  await page.goto(`${base}/jobs`);
  await select("公司筛选", "合成示例 · 云杉科技");
  await page.getByRole("button", { name: "搜索", exact: true }).click();
  await page.getByText("共 1 个职位", { exact: true }).waitFor();
  checks.push(
    "talent source filtering/reset and company job filtering through UI"
  );

  await page.goto(`${base}/imports`);
  await page.getByLabel("上传人才表格", { exact: true }).setInputFiles({
    name: "synthetic-stage-b.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "\uFEFF姓名,公司,联系方式,沟通记录,简历来源\n合成CSV人才,CSV公司,synthetic-csv,合成CSV历史沟通,合成CSV\n"
    )
  });
  await page.getByRole("combobox", { name: "工作表", exact: true }).waitFor();
  await page.getByRole("button", { name: "生成校验预览", exact: true }).click();
  await page
    .locator(".import-counts")
    .getByText("可导入 1", { exact: true })
    .waitFor();
  await page.getByRole("button", { name: "确认提交导入", exact: true }).click();
  await page
    .getByText("此批次已完成：新增 1 位，跳过 0 行。重复提交不会重复建档。", {
      exact: true
    })
    .waitFor();
  checks.push("UTF-8 BOM CSV upload, automatic mapping and real commit");

  await page.goto(`${base}/imports`);
  const matchingWorkbook = execFileSync(
    resolve("../backend/.venv/Scripts/python.exe"),
    ["-X", "utf8", "-m", "tests.template_workbook"],
    { cwd: resolve("../backend"), windowsHide: true }
  );
  await page.getByLabel("上传人才表格", { exact: true }).setInputFiles({
    name: "synthetic-matching-template.xlsx",
    mimeType:
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    buffer: matchingWorkbook
  });
  await page.getByRole("combobox", { name: "工作表", exact: true }).waitFor();
  assert.equal(await header.inputValue(), "2");
  for (const [index, label] of [
    [1, "建联日期"],
    [2, "姓名（必填）"],
    [3, "公司"],
    [4, "职位"],
    [5, "联系方式 · 电话"],
    [6, "沟通记录"],
    [7, "扩展 · 简历链接"]
  ]) {
    await page
      .locator(".el-select")
      .filter({
        has: page.getByRole("combobox", {
          name: `第${index}列对应字段`,
          exact: true
        })
      })
      .getByText(label, { exact: true })
      .waitFor();
  }
  await shot("matching-template-mapping");
  await page.getByRole("button", { name: "生成校验预览", exact: true }).click();
  await page
    .locator(".import-counts")
    .getByText("可导入 2", { exact: true })
    .waitFor();
  const matchingRow = page
    .locator(".el-table__body tr")
    .filter({ hasText: "合成模板人才" });
  await matchingRow
    .getByRole("button", { name: "修正内容", exact: true })
    .click();
  const fullUrl =
    "https://example.com/resume?reference=" + "synthetic".repeat(50);
  assert.equal(
    await page.getByLabel("修正第7列", { exact: true }).inputValue(),
    fullUrl
  );
  await page.getByLabel("修正第6列", { exact: true }).fill("合成模板已核对");
  await page
    .getByRole("button", { name: "保存并重新校验", exact: true })
    .click();
  await page
    .getByRole("dialog", { name: "修正第 3 行", exact: true })
    .waitFor({ state: "hidden" });
  await page.getByRole("button", { name: "确认提交导入", exact: true }).click();
  await page.getByRole("link", { name: "合成模板人才", exact: true }).click();
  const linkedCandidateUrl = page.url();
  const resumeLink = page
    .locator(".custom-value")
    .filter({ hasText: "简历链接" })
    .getByRole("link");
  await resumeLink.waitFor();
  assert.equal(await resumeLink.getAttribute("href"), fullUrl);
  assert.equal(await resumeLink.getAttribute("rel"), "noopener noreferrer");
  await page.getByText("电话：00123456789", { exact: true }).waitFor();
  await page.getByText("合成模板已核对", { exact: true }).waitFor();
  await shot("matching-template-talent");
  await page.goto(`${base}/candidates`);
  await page.getByRole("link", { name: "合成无日期人才", exact: true }).click();
  const unsafeValue = page
    .locator(".custom-value")
    .filter({ hasText: "简历链接" });
  await unsafeValue.getByText("javascript:alert(1)", { exact: true }).waitFor();
  assert.equal(await unsafeValue.getByRole("link").count(), 0);
  checks.push(
    "matching seven-column XLSX auto-detects row 2; dot dates, phone zeros, long hyperlink targets and safe detail links survive corrections and commit"
  );

  for (const width of [1024, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const [name, path] of [
      ["fields", "/custom-fields"],
      ["import", importUrl.replace(base, "")],
      ["linked-talent", linkedCandidateUrl.replace(base, "")],
      ["talent", candidateUrl.replace(base, "")]
    ]) {
      await page.goto(`${base}${path}`);
      await settle(page);
      const overflow = await page.evaluate(() =>
        [
          document.documentElement,
          document.body,
          document.querySelector(".hunter-content")
        ].some(el => el.scrollWidth > el.clientWidth + 1)
      );
      assert.equal(overflow, false, `${width}px ${path}`);
      if (width === 1024 || width === 1440) await shot(`${name}-${width}`);
    }
  }
  checks.push(
    "stage B fields, import/result and dynamic talent details fit all supported desktop widths"
  );
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(`${base}/candidates`);
  await settle(page);
  await writeFile(
    resolve(output, "results.json"),
    JSON.stringify({ status: "PASS", checks }, null, 2)
  );
  return { screenshots: output, checks: checks.length };
}
