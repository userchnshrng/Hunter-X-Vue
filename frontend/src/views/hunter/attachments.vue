<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { api, messageOf, type Asset } from "@/api/hunter";
import { http } from "@/utils/http";
const props = defineProps<{
  ownerType: "candidate" | "job";
  ownerId: string;
}>();
const assets = ref<Asset[]>([]);
const busy = ref(false);
async function load() {
  try {
    assets.value = await api.get<Asset[]>(
      `/files/owners/${props.ownerType}/${props.ownerId}`
    );
  } catch (e) {
    ElMessage.error(messageOf(e));
  }
}
async function upload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  busy.value = true;
  try {
    const body = new FormData();
    body.append("file", file);
    await http.request(
      "post",
      `/api/v1/files/${props.ownerType}/${props.ownerId}`,
      { data: body, timeout: 30000 }
    );
    await load();
    ElMessage.success("附件已保存");
  } catch (e) {
    ElMessage.error(messageOf(e));
  } finally {
    busy.value = false;
    input.value = "";
  }
}
async function download(asset: Asset) {
  try {
    const blob = await http.request<Blob>(
      "get",
      `/api/v1/files/${asset.id}/download`,
      { responseType: "blob" }
    );
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = asset.original_name;
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (e) {
    ElMessage.error(messageOf(e));
  }
}
onMounted(load);
</script>
<template>
  <div>
    <p class="muted" style="margin-bottom: 12px">
      附件私有保存；文字提取和简历解析将在后续阶段接入。
    </p>
    <input
      class="attachment-input"
      aria-label="上传附件"
      type="file"
      accept=".txt,.pdf,.docx,.png,.jpg,.jpeg"
      :disabled="busy"
      @change="upload"
    />
    <div v-for="asset in assets" :key="asset.id" class="record-card">
      <el-button link type="primary" @click="download(asset)">{{
        asset.original_name
      }}</el-button
      ><span class="muted"> · {{ (asset.size / 1024).toFixed(1) }} KB</span>
    </div>
  </div>
</template>
