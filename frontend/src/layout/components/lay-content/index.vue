<script setup lang="ts">
import { usePermissionStoreHook } from "@/store/modules/permission";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";
const permission = usePermissionStoreHook();
const route = useRoute();
const content = ref<HTMLElement>();
watch(
  () => route.fullPath,
  () => content.value?.scrollTo({ top: 0, left: 0 }),
  { flush: "post" }
);
</script>
<template>
  <main id="hunter-content" ref="content" class="hunter-content" tabindex="-1">
    <router-view v-slot="{ Component, route }">
      <keep-alive :include="permission.cachePageList">
        <component :is="Component" :key="route.fullPath" />
      </keep-alive>
    </router-view>
  </main>
</template>
