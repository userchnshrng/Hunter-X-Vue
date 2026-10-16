<script setup lang="ts">
import CustomFieldInputs from "./custom-field-inputs.vue";
import { pickerPopperOptions } from "./ui";
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { api, messageOf, type Candidate, type Contact } from "@/api/hunter";

const props = defineProps<{ record?: Candidate }>();
const emit = defineEmits<{ saved: [candidate: Candidate]; cancel: [] }>();
const form = reactive({
  custom_fields: { ...(props.record?.custom_fields || {}) },
  name: props.record?.name || "",
  contacted_on: props.record?.contacted_on || "",
  current_company_name: props.record?.current_company_name || "",
  current_company_id: props.record?.current_company_id || null,
  current_title: props.record?.current_title || "",
  resume_source: props.record?.resume_source || "",
  contact_methods: (props.record?.contact_methods || []).map(contact => ({
    ...contact
  })) as Contact[]
});
const busy = ref(false);
const error = ref("");
async function save() {
  if (!form.name.trim()) {
    error.value = "请填写姓名";
    return;
  }
  if (form.contact_methods.some(item => !item.value.trim())) {
    error.value = "请补全联系方式，或移除空行";
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    const body = { ...form, contacted_on: form.contacted_on || null };
    const result = props.record
      ? await api.patch<Candidate>(`/candidates/${props.record.id}`, body)
      : await api.post<Candidate>("/candidates", body);
    ElMessage.success("人才信息已保存");
    emit("saved", result);
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
    <div class="form-grid">
      <el-form-item label="姓名" required
        ><el-input v-model="form.name" aria-label="姓名" maxlength="100"
      /></el-form-item>
      <el-form-item label="建联日期"
        ><el-date-picker
          v-model="form.contacted_on"
          :popper-options="pickerPopperOptions"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="尚未建联可留空"
          style="width: 100%"
      /></el-form-item>
      <el-form-item label="当前公司"
        ><el-input
          v-model="form.current_company_name"
          aria-label="当前公司"
          @input="form.current_company_id = null"
      /></el-form-item>
      <el-form-item label="当前职位"
        ><el-input v-model="form.current_title" aria-label="当前职位"
      /></el-form-item>
      <el-form-item label="简历来源" class="full-width"
        ><el-input
          v-model="form.resume_source"
          aria-label="简历来源"
          placeholder="例如：脉脉、推荐、历史人才库"
      /></el-form-item>
    </div>
    <el-form-item label="联系方式">
      <div style="width: 100%">
        <div
          v-for="(contact, index) in form.contact_methods"
          :key="index"
          class="contact-row"
        >
          <el-select v-model="contact.type" aria-label="联系方式类型"
            ><el-option label="电话" value="phone" /><el-option
              label="微信"
              value="wechat" /><el-option
              label="邮箱"
              value="email" /><el-option
              label="其他"
              value="other" /></el-select
          ><el-input
            v-model="contact.value"
            aria-label="联系方式内容"
          /><el-button text @click="form.contact_methods.splice(index, 1)"
            >移除</el-button
          >
        </div>
        <el-button
          plain
          @click="form.contact_methods.push({ type: 'phone', value: '' })"
          >添加联系方式</el-button
        >
      </div>
    </el-form-item>
    <CustomFieldInputs v-model="form.custom_fields" entity="candidate" />
    <el-button type="primary" native-type="submit" :loading="busy"
      >保存人才</el-button
    ><el-button @click="emit('cancel')">取消</el-button>
  </el-form>
</template>
