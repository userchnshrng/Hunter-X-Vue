<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStoreHook } from "@/store/modules/user";
import { messageOf } from "@/api/hunter";
import "./style.scss";

const form = reactive({ username: "", password: "" });
const busy = ref(false);
const error = ref("");
const route = useRoute();
const router = useRouter();
async function login() {
  if (!form.username.trim() || !form.password) {
    error.value = "请输入用户名和密码";
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    await useUserStoreHook().loginByUsername({
      username: form.username.trim(),
      password: form.password
    });
    const redirect = String(route.query.redirect || "/welcome");
    await router.push(
      redirect.startsWith("/") &&
        !redirect.startsWith("//") &&
        !redirect.startsWith("/login")
        ? redirect
        : "/welcome"
    );
  } catch (value) {
    const response = value as { response?: { data?: { message?: string } } };
    error.value = response.response?.data?.message || messageOf(value);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <main class="hunter-login">
    <section class="login-story">
      <span class="brand-mark">H.</span>
      <p class="eyebrow">HUNTER WORKSPACE</p>
      <h1>把每一次沟通，<br />变成更合适的连接。</h1>
      <p>人才、职位与沟通记录，在同一个工作台中有序推进。</p>
      <div class="story-line"><span /> 为猎头日常工作而设计</div>
    </section>
    <section class="login-panel">
      <div class="login-card">
        <p class="eyebrow">欢迎回来</p>
        <h2>登录工作台</h2>
        <p class="muted">使用你的本地工作台账号继续。</p>
        <el-alert
          v-if="error"
          :title="error"
          type="error"
          :closable="false"
          show-icon
        />
        <el-form label-position="top" @submit.prevent="login">
          <el-form-item label="用户名"
            ><el-input
              v-model="form.username"
              aria-label="用户名"
              autocomplete="username"
              size="large"
          /></el-form-item>
          <el-form-item label="密码"
            ><el-input
              v-model="form.password"
              aria-label="密码"
              type="password"
              autocomplete="current-password"
              show-password
              size="large"
          /></el-form-item>
          <el-button
            native-type="submit"
            type="primary"
            size="large"
            :loading="busy"
            style="width: 100%"
            >进入工作台</el-button
          >
        </el-form>
        <div class="first-run">
          <strong>首次使用</strong>
          <p>在后端目录运行以下命令创建管理员，密码会隐藏输入。</p>
          <code>.venv\Scripts\python -m app.cli create-admin</code>
        </div>
      </div>
    </section>
  </main>
</template>
