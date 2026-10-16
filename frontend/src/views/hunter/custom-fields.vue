<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { api, messageOf, type CustomField } from "@/api/hunter";
import { useUserStoreHook } from "@/store/modules/user";
import "./style.scss";
const canEdit = computed(() => useUserStoreHook().roles.includes("admin"));
const entity = ref<"candidate" | "job">("candidate");
const fields = ref<CustomField[]>([]);
const error = ref("");
const busy = ref(false);
const editing = ref(false);
const current = ref<CustomField>();
const kinds = { text: "文本", number: "数字", date: "日期", select: "单选" };
const form = reactive({
  label: "",
  value_type: "text" as CustomField["value_type"],
  description: "",
  required: false,
  enabled: true,
  position: 0,
  options: [] as CustomField["options"]
});
const formError = ref("");
async function load() {
  busy.value = true;
  error.value = "";
  try {
    fields.value = await api.get<CustomField[]>("/custom-fields", {
      entity_type: entity.value
    });
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
function edit(field?: CustomField) {
  current.value = field;
  formError.value = "";
  Object.assign(form, {
    label: field?.label || "",
    value_type: field?.value_type || "text",
    description: field?.description || "",
    required: field?.required || false,
    enabled: field?.enabled ?? true,
    position: field?.position || 0,
    options: field?.options.map(x => ({ ...x })) || []
  });
  editing.value = true;
}
async function save() {
  busy.value = true;
  formError.value = "";
  try {
    const body = {
      ...form,
      entity_type: entity.value,
      options: form.value_type === "select" ? form.options : []
    };
    if (current.value)
      await api.patch(`/custom-fields/${current.value.id}`, {
        ...body,
        version: current.value.version
      });
    else await api.post("/custom-fields", body);
    editing.value = false;
    ElMessage.success("字段已保存");
    await load();
  } catch (e) {
    formError.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
function addOption() {
  form.options.push({ value: crypto.randomUUID(), label: "" });
}
onMounted(load);
</script>
<template>
  <div class="hunter-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">YOUR WORKSPACE FIELDS</p>
        <h1>自定义字段</h1>
        <p class="muted">把日常需要的信息，变成可维护的字段。</p>
      </div>
      <el-button v-if="canEdit" type="primary" @click="edit()"
        >新增字段</el-button
      >
    </div>
    <el-alert v-if="error" :title="error" type="error" :closable="false" />
    <section class="surface">
      <div class="toolbar">
        <el-radio-group v-model="entity" aria-label="字段归属" @change="load"
          ><el-radio-button value="candidate">人才字段</el-radio-button
          ><el-radio-button value="job"
            >职位字段</el-radio-button
          ></el-radio-group
        ><span class="muted">停用后保留历史值，类型创建后固定</span>
      </div>
      <el-table v-loading="busy" :data="fields" empty-text="还没有扩展字段"
        ><el-table-column
          label="字段名称"
          prop="label"
          min-width="160"
          show-overflow-tooltip
        /><el-table-column label="类型" width="90"
          ><template #default="{ row }">{{
            kinds[row.value_type]
          }}</template></el-table-column
        ><el-table-column label="必填" width="90"
          ><template #default="{ row }">{{
            row.required ? "是" : "否"
          }}</template></el-table-column
        ><el-table-column label="状态" width="100"
          ><template #default="{ row }"
            ><el-tag :type="row.enabled ? 'success' : 'info'">{{
              row.enabled ? "启用" : "停用"
            }}</el-tag></template
          ></el-table-column
        ><el-table-column
          label="说明"
          prop="description"
          min-width="200"
          show-overflow-tooltip
        /><el-table-column v-if="canEdit" label="操作" width="100"
          ><template #default="{ row }"
            ><span v-if="row.builtin" class="muted">固定字段</span
            ><el-button v-else link type="primary" @click="edit(row)"
              >编辑字段</el-button
            ></template
          ></el-table-column
        ></el-table
      >
    </section>
    <el-dialog
      v-model="editing"
      :title="current ? '编辑字段' : '新增字段'"
      width="min(620px,95vw)"
      destroy-on-close
    >
      <el-alert
        v-if="formError"
        :title="formError"
        type="error"
        :closable="false"
      />
      <el-form label-position="top" @submit.prevent="save"
        ><div class="form-grid">
          <el-form-item label="字段名称" required
            ><el-input
              v-model="form.label"
              aria-label="字段名称"
              maxlength="100" /></el-form-item
          ><el-form-item label="字段类型"
            ><el-select
              v-model="form.value_type"
              aria-label="字段类型"
              :disabled="!!current"
              ><el-option
                v-for="(label, key) in kinds"
                :key="key"
                :label="label"
                :value="key" /></el-select
          ></el-form-item>
        </div>
        <el-form-item label="说明"
          ><el-input
            v-model="form.description"
            aria-label="字段说明"
            maxlength="500"
        /></el-form-item>
        <div v-if="form.value_type === 'select'" class="surface nested-surface">
          <p class="muted">选项只能追加或改名，历史标识保持不变。</p>
          <div
            v-for="option in form.options"
            :key="option.value"
            class="toolbar"
          >
            <el-input
              v-model="option.label"
              aria-label="选项名称"
              maxlength="100"
            />
          </div>
          <el-button @click="addOption">添加选项</el-button>
        </div>
        <div class="toolbar">
          <el-checkbox v-model="form.required">必填字段</el-checkbox
          ><el-checkbox v-model="form.enabled">启用字段</el-checkbox
          ><el-input-number
            v-model="form.position"
            aria-label="显示顺序"
            :min="0"
            :max="10000"
          />
        </div>
        <p class="muted">设为必填后，历史记录下次保存时需要补齐。</p>
        <div class="form-actions">
          <el-button native-type="submit" type="primary" :loading="busy"
            >保存字段</el-button
          ><el-button @click="editing = false">取消</el-button>
        </div>
      </el-form>
    </el-dialog>
  </div>
</template>
