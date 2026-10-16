<script setup lang="ts">
defineProps<{ collapse?: boolean }>();
</script>
<template>
  <router-link
    to="/welcome"
    class="hunter-brand"
    aria-label="Hunter 工作台首页"
  >
    <span class="hunter-brand-mark" aria-hidden="true">h<span>.</span></span>
    <span v-if="!collapse" class="hunter-brand-copy"
      ><strong>Hunter</strong><small>猎头工作台</small></span
    >
  </router-link>
</template>
