<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  api,
  messageOf,
  type Employment,
  type Communication,
  type Fact,
  type Application
} from "@/api/hunter";
import { pickerPopperOptions } from "./ui";
const props = defineProps<{
  kind: "employment" | "communication" | "fact";
  ownerId: string;
  record: Employment | Communication | Fact;
  applications?: Application[];
}>();
const emit = defineEmits<{ saved: []; cancel: [] }>();
const source = props.record as Partial<Employment & Communication & Fact>;
const occurred = source.occurred_at;
const form = reactive({
  company_name: source.company_name || "",
  company_id: source.company_id || null,
  title: source.title || "",
  start_month: source.start_month || "",
  end_month: source.end_month || "",
  is_current: source.is_current || false,
  description: source.description || "",
  content: source.content || "",
  source: source.source || "",
  source_url: source.source_url || "",
  fact_date: source.fact_date || "",
  application_id: source.application_id || "",
  channel: source.channel || "其他",
  occurred_at: occurred
    ? new Date(/Z$|[+-]\d\d:\d\d$/.test(occurred) ? occurred : `${occurred}Z`)
    : null,
  outcome: source.outcome || "",
  next_step: source.next_step || "",
  follow_up_on: source.follow_up_on || ""
});
const error = ref("");
const busy = ref(false);
async function save() {
  busy.value = true;
  error.value = "";
  try {
    let path: string;
    let data: object;
    if (props.kind === "employment") {
      path = `/candidates/${props.ownerId}/employments/${props.record.id}`;
      data = {
        company_name: form.company_name,
        company_id: form.company_id,
        title: form.title,
        start_month: form.start_month || null,
        end_month: form.is_current ? null : form.end_month || null,
        is_current: form.is_current,
        description: form.description
      };
    } else if (props.kind === "communication") {
      path = `/candidates/${props.ownerId}/communications/${props.record.id}`;
      data = {
        application_id: form.application_id || null,
        channel: form.channel,
        content: form.content,
        occurred_at: form.occurred_at
          ? new Date(form.occurred_at).toISOString()
          : null,
        outcome: form.outcome,
        next_step: form.next_step,
        follow_up_on: form.follow_up_on || null
      };
    } else {
      path = `/companies/${props.ownerId}/facts/${props.record.id}`;
      data = {
        content: form.content,
        source: form.source,
        source_url: form.source_url,
        fact_date: form.fact_date || null
      };
    }
    await api.patch(path, data);
    ElMessage.success("记录已更新");
    emit("saved");
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
</script>
<template>
  <el-alert v-if="error" :title="error" type="error" :closable="false" />
  <el-form label-position="top" @submit.prevent="save">
    <template v-if="kind === 'employment'"
      ><el-form-item label="任职公司" required
        ><el-input
          v-model="form.company_name"
          aria-label="编辑任职公司"
          @input="form.company_id = null" /></el-form-item
      ><el-form-item label="任职职位" required
        ><el-input v-model="form.title" aria-label="编辑任职职位"
      /></el-form-item>
      <div class="form-grid">
        <el-form-item label="开始年月"
          ><el-date-picker
            v-model="form.start_month"
            :popper-options="pickerPopperOptions"
            type="month"
            value-format="YYYY-MM" /></el-form-item
        ><el-form-item label="结束年月"
          ><el-date-picker
            v-model="form.end_month"
            :popper-options="pickerPopperOptions"
            :disabled="form.is_current"
            type="month"
            value-format="YYYY-MM"
        /></el-form-item>
      </div>
      <el-checkbox v-model="form.is_current">仍在任职</el-checkbox
      ><el-form-item label="职责与业绩"
        ><el-input
          v-model="form.description"
          type="textarea"
          :rows="4" /></el-form-item
    ></template>
    <template v-else
      ><el-form-item :label="kind === 'fact' ? '资料内容' : '沟通内容'" required
        ><el-input
          v-model="form.content"
          :aria-label="kind === 'fact' ? '编辑资料内容' : '编辑沟通内容'"
          type="textarea"
          :rows="4"
      /></el-form-item>
      <template v-if="kind === 'fact'"
        ><el-form-item label="来源说明" required
          ><el-input
            v-model="form.source"
            aria-label="编辑来源说明" /></el-form-item
        ><el-form-item label="来源链接"
          ><el-input v-model="form.source_url" /></el-form-item
        ><el-form-item label="资料日期"
          ><el-date-picker
            v-model="form.fact_date"
            :popper-options="pickerPopperOptions"
            value-format="YYYY-MM-DD" /></el-form-item
      ></template>
      <template v-else
        ><div class="form-grid">
          <el-form-item label="沟通渠道"
            ><el-input v-model="form.channel" /></el-form-item
          ><el-form-item label="沟通时间"
            ><el-date-picker
              v-model="form.occurred_at"
              :popper-options="pickerPopperOptions"
              type="datetime"
          /></el-form-item>
        </div>
        <el-form-item label="关联推荐"
          ><el-select v-model="form.application_id" clearable
            ><el-option
              v-for="item in applications"
              :key="item.id"
              :value="item.id"
              :label="`${item.job_title} · ${item.company_name}`" /></el-select></el-form-item
        ><el-form-item label="沟通结果"
          ><el-input v-model="form.outcome" type="textarea" /></el-form-item
        ><el-form-item label="下一步"
          ><el-input v-model="form.next_step" /></el-form-item
        ><el-form-item label="跟进日期"
          ><el-date-picker
            v-model="form.follow_up_on"
            :popper-options="pickerPopperOptions"
            value-format="YYYY-MM-DD" /></el-form-item
      ></template>
    </template>
    <div class="form-actions">
      <el-button type="primary" native-type="submit" :loading="busy"
        >保存修改</el-button
      ><el-button @click="emit('cancel')">取消</el-button>
    </div>
  </el-form>
</template>
