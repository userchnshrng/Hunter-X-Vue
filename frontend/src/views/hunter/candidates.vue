<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, messageOf, type Candidate, type Page } from "@/api/hunter";
import CandidateEditor from "./candidate-editor.vue";
import { pickerPopperOptions } from "./ui";
import "./style.scss";
const data = ref<Page<Candidate>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20
});
const q = ref("");
const source = ref("");
const sources = ref<string[]>([]);
const contactedFrom = ref("");
const contactedTo = ref("");
const busy = ref(false);
const error = ref("");
const creating = ref(false);
async function load() {
  busy.value = true;
  error.value = "";
  try {
    data.value = await api.get<Page<Candidate>>("/candidates", {
      q: q.value,
      source: source.value,
      contacted_from: contactedFrom.value || undefined,
      contacted_to: contactedTo.value || undefined,
      page: data.value.page
    });
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
function reset() {
  q.value = "";
  source.value = "";
  contactedFrom.value = "";
  contactedTo.value = "";
  search();
}
function search() {
  data.value.page = 1;
  void load();
}
function saved() {
  creating.value = false;
  void load();
}
onMounted(async () => {
  await load();
  try {
    sources.value = await api.get<string[]>("/candidate-sources");
  } catch (e) {
    error.value = messageOf(e);
  }
});
</script>
<template>
  <div class="hunter-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">TALENT NETWORK</p>
        <h1>人才库</h1>
        <p class="muted">记录每一位人才，也保留每一次连接。</p>
      </div>
      <div class="heading-actions">
        <el-button @click="$router.push('/imports')">导入人才</el-button
        ><el-button type="primary" @click="creating = true">新增人才</el-button>
      </div>
    </div>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />
    <div class="surface">
      <form class="toolbar" @submit.prevent="search">
        <el-input
          v-model="q"
          clearable
          aria-label="搜索人才"
          placeholder="搜索姓名、公司或职位"
        /><el-select
          v-model="source"
          aria-label="简历来源筛选"
          clearable
          filterable
          allow-create
          placeholder="全部来源"
          style="width: 160px"
          ><el-option
            v-for="item in sources"
            :key="item"
            :label="item"
            :value="item" /></el-select
        ><el-date-picker
          v-model="contactedFrom"
          :popper-options="pickerPopperOptions"
          aria-label="建联开始日期"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="建联开始日期"
          style="width: 160px"
        /><el-date-picker
          v-model="contactedTo"
          :popper-options="pickerPopperOptions"
          aria-label="建联结束日期"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="建联结束日期"
          style="width: 160px"
        /><el-button native-type="submit">搜索</el-button
        ><el-button @click="reset">重置</el-button
        ><span class="muted">共 {{ data.total }} 位人才</span>
      </form>
      <el-table
        v-loading="busy"
        :data="data.items"
        empty-text="还没有人才，先添加一位开始记录"
        ><el-table-column label="姓名" min-width="150" show-overflow-tooltip
          ><template #default="{ row }"
            ><router-link :to="`/candidates/${row.id}`" class="table-name">{{
              row.name
            }}</router-link></template
          ></el-table-column
        ><el-table-column
          prop="current_company_name"
          show-overflow-tooltip
          label="当前公司"
          min-width="160" /><el-table-column
          prop="current_title"
          show-overflow-tooltip
          label="职位"
          min-width="150" /><el-table-column
          prop="contacted_on"
          label="建联日期"
          width="130" /><el-table-column label="联系方式" min-width="180"
          ><template #default="{ row }">{{
            row.contact_methods
              .map((item: { value: string }) => item.value)
              .join(" / ") || "未记录"
          }}</template></el-table-column
        ><el-table-column
          prop="resume_source"
          show-overflow-tooltip
          label="简历来源"
          width="130"
      /></el-table>
      <el-pagination
        v-model:current-page="data.page"
        class="pagination"
        :total="data.total"
        :page-size="20"
        layout="prev, pager, next"
        @current-change="load"
      />
    </div>
    <el-dialog
      v-model="creating"
      title="新增人才"
      width="min(640px,95vw)"
      destroy-on-close
      ><CandidateEditor
        v-if="creating"
        @saved="saved"
        @cancel="creating = false"
    /></el-dialog>
  </div>
</template>
