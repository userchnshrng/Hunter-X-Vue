<script setup lang="ts">
import "@/components/ReIcon/src/offlineIcon";
import { ref } from "vue";
import { useResizeObserver } from "@pureadmin/utils";
import { useAppStoreHook } from "@/store/modules/app";
import NavVertical from "./components/lay-sidebar/NavVertical.vue";
import LayNavbar from "./components/lay-navbar/index.vue";
import LayContent from "./components/lay-content/index.vue";

const app = useAppStoreHook();
const appWrapperRef = ref<HTMLDivElement>();
let previousBand = "";
useResizeObserver(appWrapperRef, entries => {
  const { width, height } = entries[0].contentRect;
  if (!width) return;
  app.setViewportSize({ width, height });
  const band = width <= 990 ? "compact" : "wide";
  if (band === previousBand) return;
  const initial = previousBand === "";
  previousBand = band;
  const opened =
    band === "wide" &&
    (initial ? app.sidebar.opened : !app.sidebar.isClickCollapse);
  app.toggleSideBar(opened, "resize");
});
</script>

<template>
  <div
    ref="appWrapperRef"
    class="hunter-shell"
    :class="{ 'is-collapsed': !app.sidebar.opened }"
  >
    <a class="skip-link" href="#hunter-content">跳到主要内容</a>
    <NavVertical />
    <div class="hunter-main">
      <LayNavbar />
      <LayContent />
    </div>
  </div>
</template>
