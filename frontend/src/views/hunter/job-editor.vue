<script setup lang="ts">
import CustomFieldInputs from "./custom-field-inputs.vue";
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  api,
  jobStatuses,
  messageOf,
  type Company,
  type Job,
  type Page
} from "@/api/hunter";
const props = defineProps<{ record?: Job }>();
const emit = defineEmits<{ saved: [job: Job]; cancel: [] }>();
const form = reactive({
  custom_fields: { ...(props.record?.custom_fields || {}) },
  company_id: props.record?.company_id || "",
  title: props.record?.title || "",
  team_size: props.record?.team_size ?? undefined,
  reports_to: props.record?.reports_to || "",
  business_context: props.record?.business_context || "",
  jd_text: props.record?.jd_text || "",
  status: props.record?.status || "open"
});
const requirements = ref(props.record?.requirements.join("\n") || "");
const companies = ref<Company[]>([]);
const busy = ref(false);
const error = ref("");
async function searchCompanies(q = "") {
  try {
    companies.value = (
      await api.get<Page<Company>>("/companies", { q, page_size: 100 })
    ).items;
  } catch (e) {
    error.value = messageOf(e);
  }
}
async function save() {
  if (!form.title.trim() || !form.company_id) {
    error.value = "请填写职位名称并选择公司";
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    const body = {
      ...form,
      team_size: form.team_size ?? null,
      requirements: requirements.value
        .split("\n")
        .map(x => x.trim())
        .filter(Boolean)
    };
    const result = props.record
      ? await api.patch<Job>(`/jobs/${props.record.id}`, body)
      : await api.post<Job>("/jobs", body);
    ElMessage.success("职位已保存");
    emit("saved", result);
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
onMounted(() => searchCompanies());
</script>
<template>
  <el-alert v-if="error" :title="error" type="error" :closable="false" />
  <el-form label-position="top" @submit.prevent="save"
    ><div class="form-grid">
      <el-form-item label="公司" required
        ><el-select
          v-model="form.company_id"
          aria-label="公司"
          filterable
          remote
          :remote-method="searchCompanies"
          placeholder="选择公司，可输入搜索"
          style="width: 100%"
          ><el-option
            v-for="item in companies"
            :key="item.id"
            :value="item.id"
            :label="item.name" /></el-select
      ></el-form-item>
      <el-form-item label="职位名称" required
        ><el-input v-model="form.title" aria-label="职位名称"
      /></el-form-item>
      <el-form-item label="下属团队人数"
        ><el-input-number
          v-model="form.team_size"
          aria-label="下属团队人数"
          :min="0"
          :precision="0"
          :max="1000000"
          controls-position="right"
          placeholder="未知可留空"
          style="width: 100%"
      /></el-form-item>
      <el-form-item label="汇报上级"
        ><el-input
          v-model="form.reports_to"
          aria-label="汇报上级"
          placeholder="职位或称谓"
      /></el-form-item>
      <el-form-item label="招聘状态"
        ><el-select v-model="form.status" style="width: 100%"
          ><el-option
            v-for="item in jobStatuses"
            :key="item[0]"
            :label="item[1]"
            :value="item[0]" /></el-select
      ></el-form-item>
      <el-form-item class="full-width" label="业务具体情况"
        ><el-input
          v-model="form.business_context"
          aria-label="业务具体情况"
          type="textarea"
          :rows="3"
      /></el-form-item>
      <el-form-item class="full-width" label="JD 原文"
        ><el-input
          v-model="form.jd_text"
          aria-label="JD 原文"
          type="textarea"
          :rows="6"
          placeholder="直接粘贴岗位 JD，此操作不调用 AI"
      /></el-form-item>
      <el-form-item class="full-width" label="已确认岗位要求"
        ><el-input
          v-model="requirements"
          type="textarea"
          :rows="3"
          placeholder="每行一条，便于后续逐项分析"
      /></el-form-item>
    </div>
    <CustomFieldInputs v-model="form.custom_fields" entity="job" />
    <el-button native-type="submit" type="primary" :loading="busy"
      >保存职位</el-button
    ><el-button @click="emit('cancel')">取消</el-button>
  </el-form>
</template>
