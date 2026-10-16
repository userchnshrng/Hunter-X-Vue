<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  api,
  messageOf,
  type Stats,
  type Page,
  type Candidate,
  type Job
} from "@/api/hunter";
import UsersIcon from "~icons/ri/group-line";
import JobIcon from "~icons/ri/briefcase-line";
import CompanyIcon from "~icons/ri/building-line";
import ConnectIcon from "~icons/ri/links-line";
import ArrowIcon from "~icons/ri/arrow-right-up-line";
import RefreshIcon from "~icons/ri/refresh-line";
import "./style.scss";
const stats = ref<Stats>();
const candidates = ref<Candidate[]>([]);
const jobs = ref<Job[]>([]);
const error = ref("");
const busy = ref(false);
async function load() {
  busy.value = true;
  error.value = "";
  try {
    const [summary, people, positions] = await Promise.all([
      api.get<Stats>("/dashboard"),
      api.get<Page<Candidate>>("/candidates", { page_size: 5 }),
      api.get<Page<Job>>("/jobs", { status: "open", page_size: 4 })
    ]);
    stats.value = summary;
    candidates.value = people.items;
    jobs.value = positions.items;
  } catch (e) {
    error.value = messageOf(e);
  } finally {
    busy.value = false;
  }
}
onMounted(load);
</script>
<template>
  <div v-loading="busy" class="hunter-page dashboard-page">
    <div class="page-heading">
      <div>
        <p class="eyebrow">YOUR RECRUITING DESK</p>
        <h1>让合适的人，遇见合适的机会</h1>
        <p class="muted">从人才信息到职位推进，保持每一步清晰可查。</p>
      </div>
      <el-button :disabled="busy" @click="load"
        ><RefreshIcon
          class="button-icon"
          aria-hidden="true"
        />刷新数据</el-button
      >
    </div>
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="false"
      show-icon
    />
    <div v-if="stats" class="stat-grid">
      <router-link
        v-for="item in [
          {
            value: stats.candidates,
            label: '人才总数',
            note: '持续积累你的人才网络',
            path: '/candidates',
            icon: UsersIcon
          },
          {
            value: stats.open_jobs,
            label: '在招职位',
            note: '正在推进的招聘机会',
            path: '/jobs',
            icon: JobIcon
          },
          {
            value: stats.companies,
            label: '合作公司',
            note: '有来源的公司与业务资料',
            path: '/companies',
            icon: CompanyIcon
          },
          {
            value: stats.applications,
            label: '职位推荐',
            note: '每位人才的独立推进记录',
            path: '/candidates',
            icon: ConnectIcon
          }
        ]"
        :key="item.label"
        :to="item.path"
        class="stat-card"
      >
        <div class="stat-top">
          <span class="stat-icon"
            ><component :is="item.icon" aria-hidden="true" /></span
          ><ArrowIcon aria-hidden="true" />
        </div>
        <span class="stat-label">{{ item.label }}</span
        ><strong>{{ item.value.toLocaleString("zh-CN") }}</strong
        ><span class="stat-note">{{ item.note }}</span>
      </router-link>
    </div>
    <div v-if="stats" class="dashboard-grid">
      <section class="surface recent-people">
        <div class="section-heading">
          <div>
            <h2>最近更新的人才</h2>
            <p class="muted">把每一次连接，留在人才网络中</p>
          </div>
          <router-link to="/candidates" class="text-link"
            >查看全部 <span aria-hidden="true">↗</span></router-link
          >
        </div>
        <div v-if="candidates.length" class="people-list">
          <router-link
            v-for="(person, index) in candidates"
            :key="person.id"
            :to="`/candidates/${person.id}`"
            class="person-row"
          >
            <span
              class="person-avatar"
              :class="`avatar-${index % 3}`"
              aria-hidden="true"
              >{{ person.name.slice(0, 1) }}</span
            >
            <span class="person-info"
              ><strong>{{ person.name }}</strong
              ><span
                >{{ person.current_company_name || "公司未记录" }} ·
                {{ person.current_title || "职位未记录" }}</span
              ></span
            >
            <span class="person-source">{{
              person.resume_source || "来源未记录"
            }}</span
            ><ArrowIcon aria-hidden="true" />
          </router-link>
        </div>
        <div v-else class="dashboard-empty">
          <UsersIcon aria-hidden="true" />
          <h3>从第一位人才开始</h3>
          <p>记录履历与沟通，让下一次联系更有依据。</p>
          <el-button @click="$router.push('/candidates')">进入人才库</el-button>
        </div>
      </section>
      <section class="surface open-positions">
        <div class="section-heading">
          <div>
            <h2>在招职位</h2>
            <p class="muted">聚焦当前的机会</p>
          </div>
          <router-link to="/jobs" class="text-link">全部 ↗</router-link>
        </div>
        <div v-if="jobs.length" class="position-list">
          <router-link
            v-for="job in jobs"
            :key="job.id"
            :to="`/jobs/${job.id}`"
            class="position-row"
            ><div class="position-top">
              <span class="position-icon"><JobIcon aria-hidden="true" /></span
              ><span class="job-badge">招聘中</span>
            </div>
            <strong>{{ job.title }}</strong>
            <p>{{ job.company_name || "公司未记录" }}</p>
            <span class="position-meta"
              >团队 {{ job.team_size ?? "待确认"
              }}<span aria-hidden="true"> · </span>汇报
              {{ job.reports_to || "待确认" }}</span
            ></router-link
          >
        </div>
        <div v-else class="dashboard-empty">
          <JobIcon aria-hidden="true" />
          <h3>新的机会，等你开启</h3>
          <p>先建立公司，再记录岗位背景与要求。</p>
          <el-button @click="$router.push('/jobs')">进入职位库</el-button>
        </div>
      </section>
    </div>
    <div class="work-grid">
      <router-link to="/candidates" class="work-card"
        ><UsersIcon aria-hidden="true" />
        <div>
          <h2>维护人才库</h2>
          <p>记录履历与每一次沟通</p>
        </div>
        <ArrowIcon aria-hidden="true"
      /></router-link>
      <router-link to="/jobs" class="work-card"
        ><JobIcon aria-hidden="true" />
        <div>
          <h2>推进职位</h2>
          <p>独立跟踪每位候选人</p>
        </div>
        <ArrowIcon aria-hidden="true"
      /></router-link>
      <router-link to="/companies" class="work-card"
        ><CompanyIcon aria-hidden="true" />
        <div>
          <h2>积累公司资料</h2>
          <p>保留信息的来源与日期</p>
        </div>
        <ArrowIcon aria-hidden="true"
      /></router-link>
    </div>
    <p class="workspace-note">
      <span class="note-dot" />当前版本 · 基础业务<span
        >Excel 导入、简历解析与 DeepSeek 分析将在后续阶段接入。</span
      >
    </p>
  </div>
</template>
