<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, messageOf, type Candidate, type Page } from "@/api/hunter";
import CandidateEditor from "./candidate-editor.vue";
import "./style.scss";
const data = ref<Page<Candidate>>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20
});
const q = ref("");
const busy = ref(false);
const error = ref("");
const creating = ref(false);
async function load() {
  busy.value = true;
  error.value = "";
  try {
    data.value = await api.get<Page<Candidate>>("/candidates", {
      q: q.value,
      page: data.value.page
    });
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
function search() {
  data.value.page = 1;
  void load();
}
function saved() {
  creating.value = false;
  void load();
}
onMounted(load);
</script>
<template>
  <div class="hunter-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">TALENT NETWORK</p>
        <h1>人才库</h1>
        <p class="muted">记录每一位人才，也保留每一次连接。</p>
      </div>
      <el-button type="primary" @click="creating = true">新增人才</el-button>
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
        /><el-button native-type="submit">搜索</el-button
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
