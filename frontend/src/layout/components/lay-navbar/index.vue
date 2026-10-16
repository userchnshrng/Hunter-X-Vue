<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useNav } from "@/layout/hooks/useNav";
import MenuIcon from "~icons/ri/menu-line";
import LogoutIcon from "~icons/ri/logout-circle-r-line";
import ArrowIcon from "~icons/ri/arrow-down-s-line";
const { device, username, logout, toggleSideBar, pureApp } = useNav();
const route = useRoute();
const date = new Intl.DateTimeFormat("zh-CN", {
  month: "long",
  day: "numeric",
  weekday: "long"
}).format(new Date());
const context = computed(() => route.meta.title || "工作台");
</script>
<template>
  <header class="hunter-navbar">
    <button
      v-if="device === 'mobile'"
      class="icon-button"
      aria-label="打开导航菜单"
      :aria-expanded="pureApp.sidebar.opened"
      @click="toggleSideBar"
    >
      <MenuIcon aria-hidden="true" />
    </button>
    <div class="navbar-context">
      <span class="navbar-section">我的工作空间</span
      ><span class="context-divider">/</span><strong>{{ context }}</strong>
    </div>
    <div class="navbar-tools">
      <span class="navbar-date">{{ date }}</span>
      <el-dropdown trigger="click">
        <button class="account-button" aria-label="账号菜单">
          <span class="account-avatar" aria-hidden="true">{{
            username?.slice(0, 1) || "H"
          }}</span>
          <span class="account-copy"
            ><strong>{{ username }}</strong
            ><small>猎头工作台</small></span
          >
          <ArrowIcon aria-hidden="true" />
        </button>
        <template #dropdown
          ><el-dropdown-menu
            ><el-dropdown-item @click="logout"
              ><LogoutIcon aria-hidden="true" />退出系统</el-dropdown-item
            ></el-dropdown-menu
          ></template
        >
      </el-dropdown>
    </div>
  </header>
</template>
