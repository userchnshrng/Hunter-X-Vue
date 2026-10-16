<script setup lang="ts">
import { computed } from "vue";
import { usePermissionStoreHook } from "@/store/modules/permission";
import { useNav } from "@/layout/hooks/useNav";
import HomeIcon from "~icons/ri/home-5-line";
import PeopleIcon from "~icons/ri/group-line";
import JobsIcon from "~icons/ri/briefcase-line";
import CompanyIcon from "~icons/ri/building-line";
import SidebarLogo from "./components/SidebarLogo.vue";
import CollapseIcon from "~icons/ri/side-bar-line";
import CloseIcon from "~icons/ri/close-line";
const props = defineProps<{ mobile?: boolean }>();
const { pureApp, toggleSideBar } = useNav();
const icons = {
  "/welcome": HomeIcon,
  "/candidates": PeopleIcon,
  "/jobs": JobsIcon,
  "/companies": CompanyIcon
};
const collapsed = computed(() => !props.mobile && !pureApp.sidebar.opened);
const menus = computed(() =>
  usePermissionStoreHook()
    .wholeMenus.flatMap(parent =>
      parent.children?.length ? parent.children : [parent]
    )
    .filter(item => item.meta?.showLink !== false)
);
</script>
<template>
  <aside
    class="hunter-sidebar"
    :class="{ 'is-collapsed': collapsed }"
    aria-label="主导航"
  >
    <div class="sidebar-brand-row">
      <SidebarLogo :collapse="collapsed" /><button
        v-if="mobile"
        class="icon-button"
        aria-label="关闭导航菜单"
        @click="toggleSideBar"
      >
        <CloseIcon aria-hidden="true" />
      </button>
    </div>
    <p class="nav-caption">{{ collapsed ? "工作" : "日常工作" }}</p>
    <nav class="hunter-nav">
      <router-link
        v-for="item in menus"
        :key="item.path"
        :to="item.path"
        class="hunter-nav-link"
        :class="{
          'is-active':
            $route.path === item.path || $route.path.startsWith(item.path + '/')
        }"
        :aria-current="
          $route.path === item.path || $route.path.startsWith(item.path + '/')
            ? 'page'
            : undefined
        "
        :title="collapsed ? String(item.meta.title) : undefined"
      >
        <component :is="icons[item.path]" aria-hidden="true" />
        <span v-if="!collapsed">{{ item.meta.title }}</span>
      </router-link>
    </nav>
    <div v-if="!collapsed" class="sidebar-note">
      <span class="note-dot" />每一次连接，都值得记录
      <p>让人才与机会有序相遇。</p>
    </div>
    <button
      v-if="!mobile"
      class="sidebar-collapse"
      :aria-label="collapsed ? '展开侧栏' : '收起侧栏'"
      :aria-expanded="!collapsed"
      @click="toggleSideBar"
    >
      <CollapseIcon aria-hidden="true" /><span v-if="!collapsed">收起侧栏</span>
    </button>
  </aside>
</template>
