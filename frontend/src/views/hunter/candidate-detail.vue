<script setup lang="ts">
import RecordEditor from "./record-editor.vue";
import type { Employment, Communication } from "@/api/hunter";
import CustomFieldInputs from "./custom-field-inputs.vue";
import { pickerPopperOptions } from "./ui";
import { reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import {
  api,
  applicationStatuses,
  dateTime,
  messageOf,
  type Candidate,
  type Job,
  type Page
} from "@/api/hunter";
import CandidateEditor from "./candidate-editor.vue";
import Attachments from "./attachments.vue";
import "./style.scss";
const route = useRoute();
const detail = ref<Candidate>();
const error = ref("");
const busy = ref(false);
const editing = ref(false);
const editingRecord = ref<{
  kind: "employment" | "communication";
  record: Employment | Communication;
}>();
const saving = ref(false);
const jobs = ref<Job[]>([]);
const selectedJob = ref("");
const communication = reactive({
  content: "",
  channel: "微信",
  outcome: "",
  next_step: "",
  follow_up_on: "",
  occurred_at: "",
  application_id: ""
});
const employment = reactive({
  company_name: "",
  company_id: null,
  title: "",
  start_month: "",
  end_month: "",
  is_current: false,
  description: ""
});
async function load() {
  busy.value = true;
  error.value = "";
  detail.value = undefined;
  try {
    detail.value = await api.get<Candidate>(
      `/candidates/${String(route.params.id)}`
    );
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
async function searchJobs(q = "") {
  try {
    jobs.value = (
      await api.get<Page<Job>>("/jobs", { q, page_size: 100 })
    ).items;
  } catch (e) {
    ElMessage.error(messageOf(e));
  }
}
async function link() {
  if (!detail.value || !selectedJob.value) return;
  saving.value = true;
  try {
    await api.post("/applications", {
      candidate_id: detail.value.id,
      job_id: selectedJob.value
    });
    selectedJob.value = "";
    await load();
    ElMessage.success("已关联职位");
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
async function addCommunication() {
  if (!detail.value) return;
  saving.value = true;
  try {
    await api.post(`/candidates/${detail.value.id}/communications`, {
      ...communication,
      application_id: communication.application_id || null,
      occurred_at: communication.occurred_at
        ? new Date(communication.occurred_at).toISOString()
        : null,
      follow_up_on: communication.follow_up_on || null
    });
    Object.assign(communication, {
      content: "",
      outcome: "",
      next_step: "",
      follow_up_on: "",
      occurred_at: "",
      application_id: ""
    });
    await load();
    ElMessage.success("沟通记录已保存");
  } catch (e) {
    ElMessage.error(messageOf(e));
  } finally {
    saving.value = false;
  }
}
async function addEmployment() {
  if (!detail.value) return;
  saving.value = true;
  try {
    await api.post(`/candidates/${detail.value.id}/employments`, {
      ...employment,
      start_month: employment.start_month || null,
      end_month: employment.is_current ? null : employment.end_month || null
    });
    Object.assign(employment, {
      company_name: "",
      title: "",
      start_month: "",
      end_month: "",
      is_current: false,
      description: ""
    });
    await load();
    ElMessage.success("任职经历已保存");
  } catch (e) {
    ElMessage.error(messageOf(e));
  } finally {
    saving.value = false;
  }
}
watch(
  () => route.params.id,
  () => {
    void load();
    void searchJobs();
  },
  { immediate: true }
);
</script>
<template>
  <div v-loading="busy" class="hunter-page">
    <el-button text @click="$router.push('/candidates')">← 返回人才库</el-button
    ><el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
    /><template v-if="detail"
      ><div class="page-heading">
        <div>
          <p class="eyebrow">TALENT PROFILE</p>
          <h1>{{ detail.name }}</h1>
          <p class="muted">
            {{ detail.current_company_name || "公司未记录" }} ·
            {{ detail.current_title || "职位未记录" }}
          </p>
        </div>
        <el-button @click="editing = true">编辑人才</el-button>
      </div>
      <CustomFieldInputs
        :model-value="detail.custom_fields"
        entity="candidate"
        readonly
      />
      <div class="detail-grid">
        <div>
          <div class="surface">
            <h2>基本信息</h2>
            <el-descriptions :column="1"
              ><el-descriptions-item label="建联日期">{{
                detail.contacted_on || "尚未记录"
              }}</el-descriptions-item
              ><el-descriptions-item label="简历来源">{{
                detail.resume_source || "尚未记录"
              }}</el-descriptions-item
              ><el-descriptions-item label="联系方式"
                ><div
                  v-for="(contact, index) in detail.contact_methods"
                  :key="index"
                >
                  {{
                    {
                      phone: "电话",
                      wechat: "微信",
                      email: "邮箱",
                      other: "其他"
                    }[contact.type]
                  }}：{{ contact.value }}
                </div>
                <span v-if="!detail.contact_methods.length"
                  >尚未记录</span
                ></el-descriptions-item
              ></el-descriptions
            >
          </div>
          <div class="surface">
            <h2>任职经历</h2>
            <p v-if="!detail.employments?.length" class="muted">
              尚未记录任职经历
            </p>
            <div
              v-for="item in detail.employments"
              :key="item.id"
              class="record-card"
            >
              <div class="record-title">
                <strong>{{ item.company_name }} · {{ item.title }}</strong
                ><el-button
                  link
                  type="primary"
                  @click="editingRecord = { kind: 'employment', record: item }"
                  >编辑经历</el-button
                >
              </div>
              <p class="muted">
                {{ item.start_month || "开始年月未知" }} —
                {{
                  item.is_current ? "至今" : item.end_month || "结束年月未知"
                }}
              </p>
              <p class="record-text">{{ item.description }}</p>
            </div>
            <el-collapse
              ><el-collapse-item title="添加任职经历" name="add"
                ><el-form label-position="top" @submit.prevent="addEmployment"
                  ><el-form-item label="任职公司" required
                    ><el-input
                      v-model="employment.company_name"
                      aria-label="任职公司" /></el-form-item
                  ><el-form-item label="任职职位" required
                    ><el-input v-model="employment.title" aria-label="任职职位"
                  /></el-form-item>
                  <div class="form-grid">
                    <el-form-item label="开始年月"
                      ><el-date-picker
                        v-model="employment.start_month"
                        :popper-options="pickerPopperOptions"
                        type="month"
                        value-format="YYYY-MM"
                        style="width: 100%" /></el-form-item
                    ><el-form-item label="结束年月"
                      ><el-date-picker
                        v-model="employment.end_month"
                        :popper-options="pickerPopperOptions"
                        type="month"
                        value-format="YYYY-MM"
                        :disabled="employment.is_current"
                        style="width: 100%"
                    /></el-form-item>
                  </div>
                  <el-checkbox v-model="employment.is_current"
                    >仍在任职</el-checkbox
                  ><el-form-item label="职责与业绩"
                    ><el-input
                      v-model="employment.description"
                      type="textarea"
                      :rows="3" /></el-form-item
                  ><el-button
                    type="primary"
                    native-type="submit"
                    :loading="saving"
                    >保存经历</el-button
                  ></el-form
                ></el-collapse-item
              ></el-collapse
            >
          </div>
          <div class="surface">
            <h2>关联职位</h2>
            <div
              v-for="item in detail.applications"
              :key="item.id"
              class="record-card"
            >
              <router-link :to="`/jobs/${item.job_id}`" class="table-name">{{
                item.job_title
              }}</router-link>
              <p class="muted" style="margin-bottom: 8px">
                {{ item.company_name }}
              </p>
              <el-select
                :model-value="item.status"
                aria-label="推荐状态"
                style="width: 150px"
                @change="(value: string) => status(item.id, value)"
                ><el-option
                  v-for="option in applicationStatuses"
                  :key="option[0]"
                  :label="option[1]"
                  :value="option[0]"
              /></el-select>
            </div>
            <div class="toolbar" style="margin-top: 16px">
              <el-select
                v-model="selectedJob"
                aria-label="关联职位"
                filterable
                remote
                :remote-method="searchJobs"
                placeholder="搜索并选择职位"
                style="width: 230px"
                ><el-option
                  v-for="job in jobs"
                  :key="job.id"
                  :label="`${job.title} · ${job.company_name}`"
                  :value="job.id" /></el-select
              ><el-button
                :loading="saving"
                :disabled="!selectedJob"
                @click="link"
                >关联职位</el-button
              >
            </div>
          </div>
          <div class="surface">
            <h2>简历附件</h2>
            <Attachments
              :key="detail.id"
              owner-type="candidate"
              :owner-id="detail.id"
            />
          </div>
        </div>
        <div>
          <div class="surface">
            <h2>追加沟通记录</h2>
            <el-form label-position="top" @submit.prevent="addCommunication"
              ><div class="form-grid">
                <el-form-item label="沟通渠道"
                  ><el-select v-model="communication.channel"
                    ><el-option
                      v-for="channel in [
                        '微信',
                        '电话',
                        '邮箱',
                        '面谈',
                        '其他'
                      ]"
                      :key="channel"
                      :value="channel"
                      :label="channel" /></el-select></el-form-item
                ><el-form-item label="沟通时间"
                  ><el-date-picker
                    v-model="communication.occurred_at"
                    :popper-options="pickerPopperOptions"
                    type="datetime"
                    placeholder="未知可留空"
                    style="width: 100%"
                /></el-form-item>
              </div>
              <el-form-item label="关联推荐"
                ><el-select
                  v-model="communication.application_id"
                  clearable
                  placeholder="可留空，作为一般沟通"
                  style="width: 100%"
                  ><el-option
                    v-for="item in detail.applications"
                    :key="item.id"
                    :value="item.id"
                    :label="`${item.job_title} · ${item.company_name}`" /></el-select></el-form-item
              ><el-form-item label="沟通内容" required
                ><el-input
                  v-model="communication.content"
                  aria-label="沟通内容"
                  type="textarea"
                  :rows="4" /></el-form-item
              ><el-form-item label="沟通结果"
                ><el-input
                  v-model="communication.outcome"
                  type="textarea"
                  :rows="2" /></el-form-item
              ><el-form-item label="下一步"
                ><el-input v-model="communication.next_step" /></el-form-item
              ><el-form-item label="跟进日期"
                ><el-date-picker
                  v-model="communication.follow_up_on"
                  :popper-options="pickerPopperOptions"
                  value-format="YYYY-MM-DD" /></el-form-item
              ><el-button type="primary" native-type="submit" :loading="saving"
                >保存沟通记录</el-button
              ></el-form
            >
          </div>
          <div class="surface">
            <h2>沟通时间线</h2>
            <el-empty
              v-if="!detail.communications?.length"
              description="尚未记录沟通"
              :image-size="65"
            />
            <div
              v-for="item in detail.communications"
              :key="item.id"
              class="record-card"
            >
              <div class="record-title">
                <strong>{{ item.channel }}</strong
                ><span class="muted">{{ dateTime(item.occurred_at) }}</span>
              </div>
              <p class="record-text">{{ item.content }}</p>
              <el-button
                link
                type="primary"
                @click="editingRecord = { kind: 'communication', record: item }"
                >编辑沟通</el-button
              >
              <p v-if="item.outcome" class="muted">结果：{{ item.outcome }}</p>
              <p v-if="item.next_step" class="muted">
                下一步：{{ item.next_step }}
              </p>
              <p v-if="item.follow_up_on" class="muted">
                跟进日期：{{ item.follow_up_on }}
              </p>
              <p v-if="!item.occurred_at" class="muted">
                记录于 {{ dateTime(item.created_at) }}
              </p>
            </div>
          </div>
        </div>
      </div>
      <el-dialog
        v-model="editing"
        title="编辑人才"
        width="min(640px,95vw)"
        destroy-on-close
        ><CandidateEditor
          v-if="editing"
          :record="detail"
          @saved="
            editing = false;
            load();
          "
          @cancel="editing = false"
      /></el-dialog>
    </template>
  </div>
  <el-dialog
    :model-value="!!editingRecord"
    :title="
      editingRecord?.kind === 'employment' ? '编辑任职经历' : '编辑沟通记录'
    "
    width="min(680px,95vw)"
    append-to-body
    destroy-on-close
    @close="editingRecord = undefined"
    ><RecordEditor
      v-if="editingRecord && detail"
      :kind="editingRecord.kind"
      :record="editingRecord.record"
      :owner-id="detail.id"
      :applications="detail.applications"
      @saved="
        editingRecord = undefined;
        load();
      "
      @cancel="editingRecord = undefined"
  /></el-dialog>
</template>
