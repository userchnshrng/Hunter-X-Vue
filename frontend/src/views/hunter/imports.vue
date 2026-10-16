<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { http } from "@/utils/http";
import {
  api,
  dateTime,
  downloadPrivate,
  messageOf,
  type CustomField,
  type ImportBatch,
  type ImportRow,
  type Page
} from "@/api/hunter";
import "./style.scss";
const route = useRoute();
const router = useRouter();
const history = ref<Page<ImportBatch>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20
});
const batch = ref<ImportBatch>();
const rows = ref<Page<ImportRow>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20
});
const fields = ref<CustomField[]>([]);
const sheet = ref("");
const header = ref(1);
const mapping = reactive<Record<string, string>>({});
const busy = ref(false);
const error = ref("");
const success = ref("");
const editing = ref<ImportRow>();
const corrections = reactive<Record<string, string>>({});
const rowError = ref("");
const rowBusy = ref(false);
const statusLabels = {
  uploaded: "待映射",
  review: "待核对",
  ready: "可提交",
  committed: "已提交",
  cancelled: "已取消"
};
const targets = computed(() => [
  { value: "name", label: "姓名（必填）" },
  { value: "contacted_on", label: "建联日期" },
  { value: "current_company_name", label: "公司" },
  { value: "current_title", label: "职位" },
  { value: "contact:phone", label: "联系方式 · 电话" },
  { value: "contact:wechat", label: "联系方式 · 微信" },
  { value: "contact:email", label: "联系方式 · 邮箱" },
  { value: "contact:other", label: "联系方式 · 其他/原文" },
  { value: "communication", label: "沟通记录" },
  { value: "resume_source", label: "简历来源" },
  ...fields.value
    .filter(f => f.enabled)
    .map(f => ({
      value: `custom:${f.key}`,
      label: `扩展 · ${f.label}${f.required ? "（必填）" : ""}`
    }))
]);
const columns = computed(
  () =>
    batch.value?.sheets
      .find(s => s.name === sheet.value)
      ?.headers.find(h => h.row === header.value)?.cells || []
);
const editable = computed(
  () => batch.value && !["committed", "cancelled"].includes(batch.value.status)
);
const mappingChanged = computed(
  () =>
    batch.value &&
    (sheet.value !== batch.value.sheet_name ||
      header.value !== batch.value.header_row ||
      JSON.stringify(
        Object.entries(mapping)
          .filter(([, v]) => v)
          .sort()
      ) !==
        JSON.stringify(
          Object.entries(batch.value.mapping)
            .filter(([, v]) => v)
            .sort()
        ))
);
const counts = computed(() => batch.value?.counts || {});
function replaceMap(
  target: Record<string, string>,
  value: Record<string, string>
) {
  Object.keys(target).forEach(key => delete target[key]);
  Object.assign(target, value);
}
async function loadHistory() {
  history.value = await api.get<Page<ImportBatch>>("/imports", {
    page: history.value.page
  });
}
async function loadRows() {
  if (batch.value?.revision)
    rows.value = await api.get<Page<ImportRow>>(
      `/imports/${batch.value.id}/rows`,
      { page: rows.value.page }
    );
}
function targetFor(name: string) {
  const aliases: Record<string, string> = {
    姓名: "name",
    名字: "name",
    建联日期: "contacted_on",
    日期: "contacted_on",
    公司: "current_company_name",
    当前公司: "current_company_name",
    职位: "current_title",
    当前职位: "current_title",
    联系方式: "contact:other",
    电话: "contact:phone",
    联系电话: "contact:phone",
    手机号码: "contact:phone",
    手机: "contact:phone",
    微信: "contact:wechat",
    邮箱: "contact:email",
    沟通记录: "communication",
    记录: "communication",
    链接: "custom:resume_link",
    简历链接: "custom:resume_link",
    简历来源: "resume_source",
    来源: "resume_source"
  };
  const label = name.trim();
  const field = fields.value.find(f => f.enabled && f.label === label);
  return aliases[label] || (field ? `custom:${field.key}` : "");
}
function suggestHeader() {
  const headers =
    batch.value?.sheets.find(s => s.name === sheet.value)?.headers || [];
  const scored = headers
    .map(row => ({
      row: row.row,
      score: new Set(row.cells.map(targetFor).filter(Boolean)).size
    }))
    .sort((a, b) => b.score - a.score || a.row - b.row);
  header.value = scored[0]?.score >= 2 ? scored[0].row : 1;
  suggest();
}
function suggest() {
  replaceMap(
    mapping,
    Object.fromEntries(
      columns.value.map((name, index) => [String(index), targetFor(name)])
    )
  );
}
async function open(id: string) {
  busy.value = true;
  error.value = "";
  success.value = "";
  try {
    batch.value = await api.get<ImportBatch>(`/imports/${id}`);
    sheet.value = batch.value.sheet_name || batch.value.sheets[0]?.name || "";
    header.value = batch.value.header_row;
    replaceMap(mapping, batch.value.mapping);
    if (!batch.value.revision) suggestHeader();
    rows.value.page = 1;
    await loadRows();
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
async function upload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  busy.value = true;
  error.value = "";
  success.value = "";
  try {
    const data = new FormData();
    data.append("file", file);
    const created = await http.request<ImportBatch>(
      "post",
      "/api/v1/imports/upload",
      { data, timeout: 30000 }
    );
    if (created.previous_batches?.length)
      ElMessage.warning("此文件曾上传过，请核对历史批次和重复提醒");
    await loadHistory();
    await router.replace({ query: { batch: created.id } });
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
    input.value = "";
  }
}
async function preview() {
  if (!batch.value) return;
  busy.value = true;
  error.value = "";
  success.value = "";
  try {
    fields.value = await api.get<CustomField[]>("/custom-fields", {
      entity_type: "candidate"
    });
    batch.value = await api.post<ImportBatch>(
      `/imports/${batch.value.id}/preview`,
      {
        revision: batch.value.revision,
        sheet_name: sheet.value,
        header_row: header.value,
        mapping: { ...mapping }
      }
    );
    rows.value.page = 1;
    await loadRows();
    await loadHistory();
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
async function updateRow(row: ImportRow, values: object) {
  if (!batch.value) return;
  batch.value = await api.patch<ImportBatch>(
    `/imports/${batch.value.id}/rows/${row.id}`,
    { revision: batch.value.revision, ...values }
  );
  await loadRows();
}
async function decision(row: ImportRow, value: string) {
  busy.value = true;
  error.value = "";
  try {
    await updateRow(row, { decision: value });
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
async function acknowledge(row: ImportRow) {
  busy.value = true;
  error.value = "";
  try {
    await updateRow(row, { acknowledged: true });
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
function editRow(row: ImportRow) {
  editing.value = row;
  rowError.value = "";
  replaceMap(
    corrections,
    Object.fromEntries(
      Object.keys(batch.value!.mapping)
        .filter(k => batch.value!.mapping[k])
        .map(k => [
          k,
          row.corrections[k] ??
            (batch.value!.mapping[k] === "custom:resume_link"
              ? (row.original[Number(k)]?.hyperlink ??
                row.original[Number(k)]?.value)
              : row.original[Number(k)]?.value) ??
            ""
        ])
    )
  );
}
async function saveRow() {
  if (!editing.value) return;
  rowBusy.value = true;
  rowError.value = "";
  try {
    await updateRow(editing.value, { corrections: { ...corrections } });
    editing.value = undefined;
  } catch (e) {
    rowError.value = messageOf(e);
  } finally {
    rowBusy.value = false;
  }
}
async function commit() {
  if (!batch.value) return;
  busy.value = true;
  error.value = "";
  try {
    const id = batch.value.id;
    const result = await api.post<{ created: number; skipped: number }>(
      `/imports/${id}/commit`,
      { revision: batch.value.revision, idempotency_key: `batch_${id}` }
    );
    await open(id);
    success.value = `导入完成：新增 ${result.created} 位人才，跳过 ${result.skipped} 行重复记录。`;
    await loadHistory();
  } catch (e) {
    error.value = messageOf(e);
    if (batch.value) {
      try {
        batch.value = await api.get<ImportBatch>(`/imports/${batch.value.id}`);
        await loadRows();
      } catch {
        /* Keep the original failure and the last visible preview on network loss. */
      }
    }
  } finally {
    busy.value = false;
  }
}
async function cancel() {
  if (!batch.value) return;
  busy.value = true;
  try {
    batch.value = await api.post<ImportBatch>(
      `/imports/${batch.value.id}/cancel`,
      {}
    );
    await loadHistory();
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
async function download(path: string, name: string) {
  try {
    await downloadPrivate(path, name);
  } catch (e) {
    error.value = messageOf(e);
  }
}
function columnLabel(column: string) {
  if (/^\d+$/.test(column))
    return `第 ${Number(column) + 1} 列 · ${columns.value[Number(column)] || "空表头"}`;
  return (
    targets.value.find(target => target.value === column)?.label ||
    (column === "custom_fields"
      ? "扩展信息"
      : column === "contact_methods"
        ? "联系方式"
        : column)
  );
}
function customSummary(row: ImportRow) {
  return Object.entries(row.normalized.candidate.custom_fields || {})
    .map(([key, value]) => {
      const field = fields.value.find(item => item.key === key);
      const display =
        field?.value_type === "select"
          ? field.options.find(item => item.value === value)?.label
          : value;
      return `${field?.label || "历史字段"}：${display ?? "未填写"}`;
    })
    .join("；");
}
async function refreshRows() {
  try {
    await loadRows();
  } catch (e) {
    error.value = messageOf(e);
  }
}
async function refreshHistory() {
  try {
    await loadHistory();
  } catch (e) {
    error.value = messageOf(e);
  }
}
watch(
  () => route.query.batch,
  id => {
    if (typeof id === "string") void open(id);
    else batch.value = undefined;
  }
);
onMounted(async () => {
  try {
    fields.value = await api.get<CustomField[]>("/custom-fields", {
      entity_type: "candidate"
    });
    await loadHistory();
    if (typeof route.query.batch === "string") await open(route.query.batch);
  } catch (e) {
    error.value = messageOf(e);
  }
});
</script>
<template>
  <div class="hunter-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">GROW YOUR TALENT NETWORK</p>
        <h1>人才导入</h1>
        <p class="muted">先预览、核对，再把人才加入你的工作台。</p>
      </div>
      <el-button @click="download('/imports/template', '人才导入模板.xlsx')"
        >下载导入模板</el-button
      >
    </div>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />
    <el-alert
      v-if="success"
      :title="success"
      type="success"
      :closable="false"
      show-icon
    />
    <section class="surface">
      <h2>上传人才表格</h2>
      <p class="muted">
        支持 .xlsx、UTF-8 CSV，最大 10 MB；每次最多 5,000 位人才、100 列。旧
        .xls 请另存为 .xlsx。只新增，不覆盖已有记录。
      </p>
      <input
        class="attachment-input"
        type="file"
        accept=".xlsx,.csv"
        aria-label="上传人才表格"
        :disabled="busy"
        @change="upload"
      />
    </section>
    <section v-if="batch" v-loading="busy" class="surface">
      <div class="section-heading">
        <div>
          <h2>{{ batch.original_name }}</h2>
          <p class="muted">
            {{ statusLabels[batch.status] }} · {{ dateTime(batch.created_at) }}
          </p>
        </div>
        <el-button
          text
          @click="download(`/imports/${batch.id}/file`, batch.original_name)"
          >下载原件</el-button
        >
      </div>
      <template v-if="editable">
        <h3 class="import-step">1. 选择工作表和表头</h3>
        <div class="form-grid">
          <el-form-item label="工作表"
            ><el-select
              v-model="sheet"
              aria-label="工作表"
              @change="suggestHeader"
              ><el-option
                v-for="item in batch.sheets"
                :key="item.name"
                :label="item.name"
                :value="item.name" /></el-select></el-form-item
          ><el-form-item label="表头所在行"
            ><el-input-number
              v-model="header"
              aria-label="表头所在行"
              :min="1"
              :max="20"
              @change="suggest"
          /></el-form-item>
        </div>
        <h3 class="import-step">2. 确认列对应关系</h3>
        <p class="muted">
          姓名必填，其他列可以忽略；多个联系方式可分别映射。自动建议需由你核对。
        </p>
        <el-table
          :data="columns.map((name, index) => ({ name, index }))"
          empty-text="这一行没有表头，请选择正确的表头行"
          ><el-table-column label="文件列" min-width="180"
            ><template #default="{ row }"
              >第 {{ row.index + 1 }} 列 · {{ row.name || "空表头" }}</template
            ></el-table-column
          ><el-table-column label="导入到" min-width="240"
            ><template #default="{ row }"
              ><el-select
                v-model="mapping[String(row.index)]"
                :aria-label="`第${row.index + 1}列对应字段`"
                clearable
                placeholder="忽略此列"
                ><el-option
                  v-for="target in targets"
                  :key="target.value"
                  :label="target.label"
                  :value="
                    target.value
                  " /></el-select></template></el-table-column
        ></el-table>
        <div class="form-actions">
          <el-button type="primary" :loading="busy" @click="preview"
            >生成校验预览</el-button
          ><el-button @click="suggest">重新建议映射</el-button>
        </div>
      </template>
      <template v-if="batch.revision">
        <h3 class="import-step">3. 核对预览和重复记录</h3>
        <p class="muted">左右滑动表格可查看联系方式、日期、沟通及扩展信息。</p>
        <el-alert
          v-if="mappingChanged && editable"
          title="映射已调整，请重新生成校验预览后再修正或提交"
          type="warning"
          :closable="false"
        />
        <div class="import-counts">
          <span>共 {{ counts.total || 0 }} 行</span
          ><span>错误 {{ counts.errors || 0 }}</span
          ><span>待核对 {{ counts.review || 0 }}</span
          ><span>跳过 {{ counts.skipped || 0 }}</span
          ><span>可导入 {{ counts.ready || 0 }}</span>
        </div>
        <el-table :data="rows.items" empty-text="没有预览数据"
          ><el-table-column
            prop="row_number"
            label="原行号"
            width="90" /><el-table-column
            label="姓名 / 当前公司"
            min-width="200"
            ><template #default="{ row }"
              ><router-link
                v-if="row.candidate_id"
                :to="`/candidates/${row.candidate_id}`"
                class="table-name"
                >{{ row.normalized.candidate.name }}</router-link
              ><strong v-else>{{
                row.normalized.candidate.name || "姓名缺失"
              }}</strong>
              <p class="muted">
                {{ row.normalized.candidate.current_company_name }}
              </p></template
            ></el-table-column
          ><el-table-column
            label="职位 / 联系方式"
            min-width="220"
            show-overflow-tooltip
            ><template #default="{ row }"
              ><p>
                {{ row.normalized.candidate.current_title || "职位未填写" }}
              </p>
              <p class="muted">
                {{
                  row.normalized.candidate.contact_methods
                    ?.map(item => item.value)
                    .join(" / ") || "联系方式未填写"
                }}
              </p></template
            ></el-table-column
          >
          <el-table-column
            label="建联日期 / 来源"
            min-width="180"
            show-overflow-tooltip
            ><template #default="{ row }"
              ><p>
                {{ row.normalized.candidate.contacted_on || "建联日期未知" }}
              </p>
              <p class="muted">
                {{ row.normalized.candidate.resume_source || "来源未填写" }}
              </p></template
            ></el-table-column
          >
          <el-table-column
            label="沟通与扩展信息"
            min-width="260"
            show-overflow-tooltip
            ><template #default="{ row }"
              ><p>{{ row.normalized.communication || "沟通未填写" }}</p>
              <p class="muted">{{ customSummary(row) }}</p></template
            ></el-table-column
          >
          <el-table-column label="校验与重复提醒" min-width="300"
            ><template #default="{ row }"
              ><p
                v-for="(item, index) in row.errors"
                :key="`e${index}`"
                class="import-error"
              >
                {{ columnLabel(item.column) }}：{{ item.message }}
              </p>
              <p
                v-for="(item, index) in row.warnings"
                :key="`w${index}`"
                class="import-warning"
              >
                {{ item.message }}
              </p>
              <p v-if="row.duplicates.length" class="import-warning">
                可能重复：{{
                  row.duplicates
                    .map(item =>
                      item.kind === "batch"
                        ? `本批第 ${item.row} 行`
                        : `库内 ${item.name}`
                    )
                    .join("；")
                }}
              </p>
              <span
                v-if="
                  !row.errors.length &&
                  !row.warnings.length &&
                  !row.duplicates.length
                "
                class="muted"
                >校验通过</span
              ><span v-if="row.status === 'created'" class="muted">
                · 已新增</span
              ></template
            ></el-table-column
          ><el-table-column v-if="editable" label="核对操作" min-width="240"
            ><template #default="{ row }"
              ><div class="preview-actions">
                <el-button
                  link
                  type="primary"
                  :disabled="mappingChanged || busy"
                  @click="editRow(row)"
                  >修正内容</el-button
                ><el-button
                  v-if="row.warnings.length && !row.acknowledged"
                  link
                  :disabled="mappingChanged || busy"
                  @click="acknowledge(row)"
                  >已核对提醒</el-button
                ><el-select
                  v-if="row.duplicates.length"
                  :model-value="row.decision"
                  :aria-label="`第${row.row_number}行重复处理`"
                  :disabled="mappingChanged || busy"
                  placeholder="选择重复处理"
                  @change="decision(row, $event)"
                  ><el-option label="仍然新建" value="create" /><el-option
                    label="跳过重复行"
                    value="skip"
                /></el-select></div></template></el-table-column
        ></el-table>
        <el-pagination
          v-model:current-page="rows.page"
          class="pagination"
          :total="rows.total"
          :page-size="20"
          layout="prev,pager,next"
          @current-change="refreshRows"
        />
        <div class="form-actions">
          <el-button
            @click="download(`/imports/${batch.id}/errors`, '导入校验报告.csv')"
            >下载校验报告</el-button
          ><el-button
            v-if="editable"
            type="primary"
            :disabled="batch.status !== 'ready' || mappingChanged"
            :loading="busy"
            @click="commit"
            >确认提交导入</el-button
          ><el-button v-if="editable" :disabled="busy" @click="cancel"
            >取消此批次</el-button
          >
        </div>
      </template>
      <el-alert
        v-if="batch.status === 'committed'"
        :title="`此批次已完成：新增 ${batch.result.created} 位，跳过 ${batch.result.skipped} 行。重复提交不会重复建档。`"
        type="success"
        :closable="false"
      />
    </section>
    <section class="surface">
      <h2>我的导入记录</h2>
      <el-table :data="history.items" empty-text="还没有导入记录"
        ><el-table-column label="文件" min-width="220" show-overflow-tooltip
          ><template #default="{ row }"
            ><el-button
              link
              type="primary"
              @click="$router.replace({ query: { batch: row.id } })"
              >{{ row.original_name }}</el-button
            ></template
          ></el-table-column
        ><el-table-column label="状态" width="110"
          ><template #default="{ row }">{{
            statusLabels[row.status]
          }}</template></el-table-column
        ><el-table-column label="上传时间" min-width="180"
          ><template #default="{ row }">{{
            dateTime(row.created_at)
          }}</template></el-table-column
        ></el-table
      ><el-pagination
        v-model:current-page="history.page"
        class="pagination"
        :total="history.total"
        :page-size="20"
        layout="prev,pager,next"
        @current-change="refreshHistory"
      />
    </section>
    <el-dialog
      :model-value="!!editing"
      :title="`修正第 ${editing?.row_number} 行`"
      width="min(680px,95vw)"
      @close="editing = undefined"
      ><el-alert
        v-if="rowError"
        :title="rowError"
        type="error"
        :closable="false"
      /><el-form label-position="top" @submit.prevent="saveRow"
        ><el-form-item
          v-for="column in Object.keys(corrections)"
          :key="column"
          :label="`第 ${Number(column) + 1} 列 · ${targets.find(t => t.value === batch?.mapping[column])?.label || columns[Number(column)]}`"
          ><el-input
            v-model="corrections[column]"
            :aria-label="`修正第${Number(column) + 1}列`"
            maxlength="20000" /></el-form-item
        ><el-button type="primary" native-type="submit" :loading="rowBusy"
          >保存并重新校验</el-button
        ><el-button @click="editing = undefined">取消</el-button></el-form
      ></el-dialog
    >
  </div>
</template>
