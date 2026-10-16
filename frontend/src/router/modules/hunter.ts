const Layout = () => import("@/layout/index.vue");

export default {
  path: "/business",
  name: "Business",
  component: Layout,
  redirect: "/candidates",
  meta: { title: "猎头业务", icon: "ep/briefcase", rank: 1 },
  children: [
    {
      path: "/imports",
      name: "Imports",
      component: () => import("@/views/hunter/imports.vue"),
      meta: { title: "人才导入", icon: "ep/upload" }
    },
    {
      path: "/custom-fields",
      name: "CustomFields",
      component: () => import("@/views/hunter/custom-fields.vue"),
      meta: { title: "自定义字段", icon: "ep/setting" }
    },
    {
      path: "/candidates",
      name: "Candidates",
      component: () => import("@/views/hunter/candidates.vue"),
      meta: { title: "人才库", icon: "ep/user" }
    },
    {
      path: "/candidates/:id",
      name: "CandidateDetail",
      component: () => import("@/views/hunter/candidate-detail.vue"),
      meta: { title: "人才详情", showLink: false }
    },
    {
      path: "/jobs",
      name: "Jobs",
      component: () => import("@/views/hunter/jobs.vue"),
      meta: { title: "职位库", icon: "ep/suitcase" }
    },
    {
      path: "/jobs/:id",
      name: "JobDetail",
      component: () => import("@/views/hunter/job-detail.vue"),
      meta: { title: "职位详情", showLink: false }
    },
    {
      path: "/companies",
      name: "Companies",
      component: () => import("@/views/hunter/companies.vue"),
      meta: { title: "公司资料", icon: "ep/office-building" }
    }
  ]
} satisfies RouteConfigsTable;
