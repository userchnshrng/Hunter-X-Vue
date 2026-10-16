<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import {
  api,
  applicationStatuses,
  jobStatuses,
  messageOf,
  type Candidate,
  type Job,
  type Page
} from "@/api/hunter";
import JobEditor from "./job-editor.vue";
import Attachments from "./attachments.vue";
import "./style.scss";
const route = useRoute();
const detail = ref<Job>();
const busy = ref(false);
const error = ref("");
const editing = ref(false);
const candidates = ref<Candidate[]>([]);
const selected = ref("");
const saving = ref(false);
async function load() {
  busy.value = true;
  error.value = "";
  detail.value = undefined;
  try {
    detail.value = await api.get<Job>(`/jobs/${String(route.params.id)}`);
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
async function searchCandidates(q = "") {
  try {
    candidates.value = (
      await api.get<Page<Candidate>>("/candidates", { q, page_size: 100 })
    ).items;
  } catch (e) {
    ElMessage.error(messageOf(e));
  }
}
async function link() {
  if (!detail.value || !selected.value) return;
  saving.value = true;
  try {
    await api.post("/applications", {
      candidate_id: selected.value,
      job_id: detail.value.id
    });
    selected.value = "";
    await load();
    ElMessage.success("人才已关联");
  } catch (e) {
    ElMessage.error(messageOf(e));
  } finally {
    saving.value = false;
  }
}
async function status(id: string, value: string) {
  try {
    await api.patch(`/applications/${id}`, { status: value });
    await load();
  } catch (e) {
    ElMessage.error(messageOf(e));
  }
}
watch(
  () => route.params.id,
  () => {
    void load();
    void searchCandidates();
  },
  { immediate: true }
);
</script>
<template>
  <div v-loading="busy" class="hunter-page">
    <el-button text @click="$router.push('/jobs')">← 返回职位库</el-button
    ><el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
    /><template v-if="detail"
      ><div class="page-heading">
        <div>
          <p class="eyebrow">POSITION BRIEF</p>
          <h1>{{ detail.title }}</h1>
          <p class="muted">
            {{ detail.company_name }} ·
            {{ jobStatuses.find(item => item[0] === detail?.status)?.[1] }}
          </p>
        </div>
        <el-button @click="editing = true">编辑职位</el-button>
      </div>
      <div class="detail-grid">
        <div>
          <div class="surface">
            <h2>岗位背景</h2>
            <el-descriptions :column="1"
              ><el-descriptions-item label="下属团队人数">{{
                detail.team_size ?? "未知"
              }}</el-descriptions-item
              ><el-descriptions-item label="汇报上级">{{
                detail.reports_to || "未记录"
              }}</el-descriptions-item></el-descriptions
            >
            <p class="muted" style="margin: 15px 0 5px">业务具体情况</p>
            <p class="record-text">
              {{ detail.business_context || "尚未记录" }}
            </p>
          </div>
          <div class="surface">
            <h2>JD 原文</h2>
            <p class="record-text">{{ detail.jd_text || "尚未录入 JD" }}</p>
            <h2 style="margin-top: 25px">已确认岗位要求</h2>
            <p
              v-for="(requirement, index) in detail.requirements"
              :key="index"
              class="record-text"
            >
              {{ index + 1 }}. {{ requirement }}
            </p>
            <p v-if="!detail.requirements.length" class="muted">
              尚未单独确认岗位要求
            </p>
          </div>
          <div class="surface">
            <h2>岗位附件</h2>
            <Attachments
              :key="detail.id"
              owner-type="job"
              :owner-id="detail.id"
            />
          </div>
        </div>
        <div>
          <div class="surface">
            <h2>推荐人才</h2>
            <div class="toolbar">
              <el-select
                v-model="selected"
                filterable
                remote
                :remote-method="searchCandidates"
                placeholder="搜索并选择人才"
                style="width: 210px"
                ><el-option
                  v-for="item in candidates"
                  :key="item.id"
                  :label="`${item.name} · ${item.current_company_name}`"
                  :value="item.id" /></el-select
              ><el-button :disabled="!selected" :loading="saving" @click="link"
                >关联人才</el-button
              >
            </div>
            <el-empty
              v-if="!detail.applications?.length"
              description="尚未关联候选人"
              :image-size="65"
            />
            <div
              v-for="item in detail.applications"
              :key="item.id"
              class="record-card"
            >
              <div class="record-title">
                <router-link
                  :to="`/candidates/${item.candidate_id}`"
                  class="table-name"
                  >{{ item.candidate_name }}</router-link
                ><el-select
                  :model-value="item.status"
                  style="width: 135px"
                  @change="(value: string) => status(item.id, value)"
                  ><el-option
                    v-for="option in applicationStatuses"
                    :key="option[0]"
                    :label="option[1]"
                    :value="option[0]"
                /></el-select>
              </div>
            </div>
          </div>
          <div class="workspace-note">
            <strong>独立推进每一条推荐</strong>
            <p>
              人才关联其他职位时，沟通状态分别保存。DeepSeek
              匹配与话术将在后续阶段接入。
            </p>
          </div>
        </div>
      </div>
      <el-dialog
        v-model="editing"
        title="编辑职位"
        width="min(740px,95vw)"
        destroy-on-close
        ><JobEditor
          v-if="editing"
          :record="detail"
          @saved="
            editing = false;
            load();
          "
          @cancel="editing = false" /></el-dialog
    ></template>
  </div>
</template>
