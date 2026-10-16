<script setup lang="ts">
import "@/components/ReIcon/src/offlineIcon";
import { ref, computed, watch } from "vue";
import { useRoute } from "vue-router";
import { useResizeObserver } from "@pureadmin/utils";
import { useAppStoreHook } from "@/store/modules/app";
import NavVertical from "./components/lay-sidebar/NavVertical.vue";
import LayNavbar from "./components/lay-navbar/index.vue";
import LayContent from "./components/lay-content/index.vue";

const app = useAppStoreHook();
const route = useRoute();
const appWrapperRef = ref<HTMLDivElement>();
const mobile = computed(() => app.device === "mobile");
const drawer = computed({
  get: () => mobile.value && app.sidebar.opened,
  set: (opened: boolean) => app.toggleSideBar(opened, "resize")
});
let previousBand = "";
useResizeObserver(appWrapperRef, entries => {
  const { width, height } = entries[0].contentRect;
  if (!width) return;
  app.setViewportSize({ width, height });
  const band = width <= 760 ? "mobile" : width <= 990 ? "compact" : "wide";
  if (band === previousBand) return;
  const initial = previousBand === "";
  previousBand = band;
  app.toggleDevice(band === "mobile" ? "mobile" : "desktop");
  const opened =
    band === "wide" &&
    (initial ? app.sidebar.opened : !app.sidebar.isClickCollapse);
  app.toggleSideBar(opened, "resize");
});
watch(
  () => route.path,
  () => {
    if (mobile.value) drawer.value = false;
  }
);
</script>

<template>
  <div
    ref="appWrapperRef"
    class="hunter-shell"
    :class="{ 'is-collapsed': !app.sidebar.opened, 'is-mobile': mobile }"
  >
    <a class="skip-link" href="#hunter-content">跳到主要内容</a>
    <NavVertical v-if="!mobile" />
    <el-drawer
      v-model="drawer"
      class="hunter-nav-drawer"
      direction="ltr"
      size="260px"
      title="导航菜单"
      :with-header="false"
      append-to-body
    >
      <NavVertical mobile />
    </el-drawer>
    <div class="hunter-main">
      <LayNavbar />
      <LayContent />
    </div>
  </div>
</template>
