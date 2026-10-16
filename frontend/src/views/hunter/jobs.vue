<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, jobStatuses, messageOf, type Job, type Page } from "@/api/hunter";
import JobEditor from "./job-editor.vue";
import "./style.scss";
const data = ref<Page<Job>>({ items: [], total: 0, page: 1, page_size: 20 });
const q = ref("");
const status = ref("");
const busy = ref(false);
const error = ref("");
const creating = ref(false);
async function load() {
  busy.value = true;
  error.value = "";
  try {
    data.value = await api.get<Page<Job>>("/jobs", {
      q: q.value,
      status: status.value,
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
        <p class="eyebrow">OPPORTUNITIES</p>
        <h1>职位库</h1>
        <p class="muted">把岗位背景和要求写清楚，推进每一个机会。</p>
      </div>
      <el-button type="primary" @click="creating = true">新增职位</el-button>
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
          aria-label="搜索职位"
          placeholder="搜索职位名称"
        /><el-select
          v-model="status"
          clearable
          placeholder="全部状态"
          style="width: 140px"
          ><el-option
            v-for="item in jobStatuses"
            :key="item[0]"
            :label="item[1]"
            :value="item[0]" /></el-select
        ><el-button native-type="submit">搜索</el-button
        ><span class="muted">共 {{ data.total }} 个职位</span>
      </form>
      <el-table
        v-loading="busy"
        :data="data.items"
        empty-text="还没有职位，可先在公司资料中建立公司"
        ><el-table-column label="职位名称" min-width="180" show-overflow-tooltip
          ><template #default="{ row }"
            ><router-link :to="`/jobs/${row.id}`" class="table-name">{{
              row.title
            }}</router-link></template
          ></el-table-column
        ><el-table-column
          prop="company_name"
          show-overflow-tooltip
          label="公司"
          min-width="180"
        /><el-table-column label="团队人数" width="120"
          ><template #default="{ row }">{{
            row.team_size ?? "未知"
          }}</template></el-table-column
        ><el-table-column
          prop="reports_to"
          show-overflow-tooltip
          label="汇报上级"
          min-width="140"
        /><el-table-column label="状态" width="110"
          ><template #default="{ row }"
            ><el-tag :type="row.status === 'open' ? 'success' : 'info'">{{
              jobStatuses.find(item => item[0] === row.status)?.[1]
            }}</el-tag></template
          ></el-table-column
        ></el-table
      >
      <el-pagination
        v-model:current-page="data.page"
        class="pagination"
        :total="data.total"
        :page-size="20"
        layout="prev,pager,next"
        @current-change="load"
      />
    </div>
    <el-dialog
      v-model="creating"
      title="新增职位"
      width="min(740px,95vw)"
      destroy-on-close
      ><JobEditor v-if="creating" @saved="saved" @cancel="creating = false"
    /></el-dialog>
  </div>
</template>
