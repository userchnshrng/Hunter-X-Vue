<script setup lang="ts">
import { onMounted, ref } from "vue";
import { api, messageOf, type CustomField } from "@/api/hunter";
import { pickerPopperOptions } from "./ui";
const props = defineProps<{
  entity: "candidate" | "job";
  modelValue: Record<string, string | number | null>;
  readonly?: boolean;
}>();
const emit = defineEmits<{
  "update:modelValue": [value: Record<string, string | number | null>];
}>();
const fields = ref<CustomField[]>([]);
const error = ref("");
const loading = ref(true);
function change(key: string, value: string | number | null | undefined) {
  emit("update:modelValue", { ...props.modelValue, [key]: value ?? null });
}
onMounted(async () => {
  try {
    fields.value = await api.get<CustomField[]>("/custom-fields", {
      entity_type: props.entity
    });
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    loading.value = false;
  }
});
function display(field: CustomField) {
  const value = props.modelValue[field.key];
  return field.value_type === "select"
    ? field.options.find(option => option.value === value)?.label || value
    : value;
}
function resumeHref(field: CustomField) {
  if (field.key !== "resume_link") return undefined;
  const value = props.modelValue[field.key];
  if (typeof value !== "string") return undefined;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}
</script>
<template>
  <div v-if="loading" class="muted">正在读取扩展字段…</div>
  <el-alert v-if="error" :title="error" type="error" :closable="false" />
  <div
    v-if="fields.length"
    class="custom-fields-block"
    :class="{ surface: readonly }"
  >
    <h2>扩展信息</h2>
    <template v-if="readonly">
      <div
        v-for="field in fields.filter(
          f => f.enabled || modelValue[f.key] != null
        )"
        :key="field.key"
        class="custom-value"
      >
        <span>{{ field.label }}{{ field.enabled ? "" : "（已停用）" }}</span
        ><strong
          ><a
            v-if="resumeHref(field)"
            :href="resumeHref(field)"
            target="_blank"
            rel="noopener noreferrer"
            >{{ display(field) }}</a
          ><template v-else>{{ display(field) ?? "未填写" }}</template></strong
        >
      </div>
    </template>
    <div v-else class="form-grid">
      <el-form-item
        v-for="field in fields.filter(f => f.enabled)"
        :key="field.key"
        :label="field.label"
        :required="field.required"
      >
        <el-input
          v-if="field.value_type === 'text'"
          :model-value="String(modelValue[field.key] ?? '')"
          :aria-label="field.label"
          maxlength="2000"
          @update:model-value="change(field.key, $event)"
        />
        <el-input-number
          v-else-if="field.value_type === 'number'"
          :model-value="
            typeof modelValue[field.key] === 'number'
              ? Number(modelValue[field.key])
              : undefined
          "
          :aria-label="field.label"
          controls-position="right"
          style="width: 100%"
          @update:model-value="change(field.key, $event)"
        />
        <el-date-picker
          v-else-if="field.value_type === 'date'"
          :model-value="modelValue[field.key] || undefined"
          :popper-options="pickerPopperOptions"
          :aria-label="field.label"
          type="date"
          value-format="YYYY-MM-DD"
          style="width: 100%"
          @update:model-value="change(field.key, $event)"
        />
        <el-select
          v-else
          :model-value="modelValue[field.key]"
          :aria-label="field.label"
          clearable
          @update:model-value="change(field.key, $event)"
          ><el-option
            v-for="option in field.options"
            :key="option.value"
            :label="option.label"
            :value="option.value"
        /></el-select>
        <p v-if="field.description" class="muted">{{ field.description }}</p>
      </el-form-item>
    </div>
  </div>
</template>
