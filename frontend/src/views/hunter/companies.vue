<script setup lang="ts">
import RecordEditor from "./record-editor.vue";
import type { Fact } from "@/api/hunter";
import { pickerPopperOptions } from "./ui";
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  api,
  dateTime,
  messageOf,
  type Company,
  type Page
} from "@/api/hunter";
import "./style.scss";
const data = ref<Page<Company>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20
});
const q = ref("");
const error = ref("");
const busy = ref(false);
const saving = ref(false);
const editing = ref(false);
const detail = ref<Company>();
const editingFact = ref<Fact>();
const companyId = ref("");
const form = reactive({
  name: "",
  industry: "",
  description: "",
  aliases: [] as string[]
});
const fact = reactive({
  content: "",
  source: "",
  source_url: "",
  fact_date: ""
});
async function load() {
  busy.value = true;
  error.value = "";
  try {
    data.value = await api.get<Page<Company>>("/companies", {
      q: q.value,
      page: data.value.page
    });
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
function edit(record?: Company) {
  companyId.value = record?.id || "";
  Object.assign(form, {
    name: record?.name || "",
    industry: record?.industry || "",
    description: record?.description || "",
    aliases: record?.aliases || []
  });
  editing.value = true;
}
async function save() {
  if (!form.name.trim()) {
    ElMessage.error("请填写公司名称");
    return;
  }
  saving.value = true;
  try {
    if (companyId.value) await api.patch(`/companies/${companyId.value}`, form);
    else await api.post("/companies", form);
    editing.value = false;
    ElMessage.success("公司已保存");
    await load();
  } catch (e) {
    ElMessage.error(messageOf(e));
  } finally {
    saving.value = false;
  }
}
async function show(id: string) {
  try {
    detail.value = await api.get<Company>(`/companies/${id}`);
  } catch (e) {
    ElMessage.error(messageOf(e));
  }
}
async function saveFact() {
  if (!detail.value) return;
  saving.value = true;
  try {
    await api.post(`/companies/${detail.value.id}/facts`, {
      ...fact,
      fact_date: fact.fact_date || null
    });
    Object.assign(fact, {
      content: "",
      source: "",
      source_url: "",
      fact_date: ""
    });
    await show(detail.value.id);
    ElMessage.success("资料已记录");
  } catch (e) {
    ElMessage.error(messageOf(e));
  } finally {
    saving.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div class="hunter-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">COMPANY INTELLIGENCE</p>
        <h1>公司资料</h1>
        <p class="muted">保留事实的来源与日期，为后续沟通提供依据。</p>
      </div>
      <el-button type="primary" @click="edit()">新增公司</el-button>
    </div>
    <el-alert v-if="error" :title="error" type="error" :closable="false" />
    <div class="surface">
      <form
        class="toolbar"
        @submit.prevent="
          data.page = 1;
          load();
        "
      >
        <el-input
          v-model="q"
          aria-label="搜索公司"
          placeholder="搜索公司名称"
          clearable
        /><el-button native-type="submit">搜索</el-button>
      </form>
      <el-table
        v-loading="busy"
        :data="data.items"
        empty-text="先添加一家合作公司"
        ><el-table-column label="公司名称" min-width="200"
          ><template #default="{ row }"
            ><el-button link class="table-name" @click="show(row.id)">{{
              row.name
            }}</el-button></template
          ></el-table-column
        ><el-table-column
          prop="industry"
          label="行业"
          min-width="130"
        /><el-table-column
          prop="description"
          label="业务简介"
          min-width="250"
          show-overflow-tooltip
        /><el-table-column label="操作" width="100"
          ><template #default="{ row }"
            ><el-button link type="primary" @click="edit(row)"
              >编辑</el-button
            ></template
          ></el-table-column
        ></el-table
      ><el-pagination
        v-model:current-page="data.page"
        class="pagination"
        :total="data.total"
        :page-size="20"
        layout="prev,pager,next"
        @current-change="load"
      />
    </div>
    <el-dialog
      v-model="editing"
      :title="companyId ? '编辑公司' : '新增公司'"
      width="min(620px,95vw)"
      ><el-form label-position="top" @submit.prevent="save"
        ><el-form-item label="公司名称" required
          ><el-input v-model="form.name" aria-label="公司名称" /></el-form-item
        ><el-form-item label="行业"
          ><el-input v-model="form.industry" aria-label="行业" /></el-form-item
        ><el-form-item label="业务简介"
          ><el-input
            v-model="form.description"
            aria-label="业务简介"
            type="textarea"
            :rows="4" /></el-form-item
        ><el-button type="primary" native-type="submit" :loading="saving"
          >保存公司</el-button
        ></el-form
      ></el-dialog
    >
    <el-drawer
      :model-value="Boolean(detail)"
      size="min(650px,95vw)"
      :title="detail?.name"
      @close="detail = undefined"
      ><template v-if="detail"
        ><p class="record-text">
          {{ detail.description || "尚未记录业务简介" }}
        </p>
        <el-divider>公司近况与事实资料</el-divider>
        <p v-if="!detail.facts?.length" class="muted">
          暂无资料。后续生成话术时不会自动编造公司近况。
        </p>
        <div v-for="item in detail.facts" :key="item.id" class="record-card">
          <p class="record-text">{{ item.content }}</p>
          <el-button link type="primary" @click="editingFact = item"
            >编辑资料</el-button
          >
          <p class="muted">
            资料日期：{{ item.fact_date || "未知" }} · 来源：{{ item.source }}
          </p>
          <a
            v-if="item.source_url"
            :href="item.source_url"
            target="_blank"
            rel="noopener noreferrer"
            class="table-name"
            >查看来源 ↗</a
          >
          <p class="muted">录入于 {{ dateTime(item.created_at) }}</p>
        </div>
        <el-divider>追加资料</el-divider
        ><el-form label-position="top" @submit.prevent="saveFact"
          ><el-form-item label="资料内容" required
            ><el-input
              v-model="fact.content"
              aria-label="资料内容"
              type="textarea"
              :rows="4" /></el-form-item
          ><el-form-item label="来源说明" required
            ><el-input
              v-model="fact.source"
              aria-label="来源说明"
              placeholder="公司官网、公告或人工沟通记录等" /></el-form-item
          ><el-form-item label="来源链接"
            ><el-input v-model="fact.source_url" /></el-form-item
          ><el-form-item label="资料日期"
            ><el-date-picker
              v-model="fact.fact_date"
              :popper-options="pickerPopperOptions"
              value-format="YYYY-MM-DD"
              placeholder="不知道可留空" /></el-form-item
          ><el-button type="primary" native-type="submit" :loading="saving"
            >记录资料</el-button
          ></el-form
        ></template
      ></el-drawer
    >
  </div>
  <el-dialog
    :model-value="!!editingFact"
    title="编辑公司资料"
    width="min(640px,95vw)"
    append-to-body
    destroy-on-close
    @close="editingFact = undefined"
    ><RecordEditor
      v-if="editingFact && detail"
      kind="fact"
      :record="editingFact"
      :owner-id="detail.id"
      @saved="
        editingFact = undefined;
        show(detail.id);
      "
      @cancel="editingFact = undefined"
  /></el-dialog>
</template>
