import { http } from "@/utils/http";

export interface Contact {
  type: "phone" | "wechat" | "email" | "other";
  value: string;
}
export interface Company {
  id: string;
  name: string;
  aliases: string[];
  industry: string;
  description: string;
  facts?: Fact[];
}
export interface Fact {
  id: string;
  content: string;
  source: string;
  source_url: string;
  fact_date: string | null;
  created_at: string;
}
export interface Candidate {
  id: string;
  name: string;
  contacted_on: string | null;
  current_company_id: string | null;
  current_company_name: string;
  current_title: string;
  contact_methods: Contact[];
  resume_source: string;
  employments?: Employment[];
  communications?: Communication[];
  applications?: Application[];
}
export interface Employment {
  id: string;
  company_id: string | null;
  company_name: string;
  title: string;
  start_month: string | null;
  end_month: string | null;
  is_current: boolean;
  description: string;
}
export interface Job {
  id: string;
  company_id: string;
  company_name?: string;
  title: string;
  team_size: number | null;
  reports_to: string;
  business_context: string;
  jd_text: string;
  requirements: string[];
  status: string;
  applications?: Application[];
}
export interface Application {
  id: string;
  candidate_id: string;
  job_id: string;
  status: string;
  candidate_name: string;
  job_title: string;
  company_name: string;
}
export interface Communication {
  id: string;
  application_id: string | null;
  occurred_at: string | null;
  channel: string;
  content: string;
  outcome: string;
  next_step: string;
  follow_up_on: string | null;
  created_at: string;
}
export interface Asset {
  id: string;
  original_name: string;
  size: number;
  parse_status: string;
}
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
export interface Stats {
  candidates: number;
  companies: number;
  open_jobs: number;
  applications: number;
  follow_ups: number;
}

export const api = {
  get: <T>(path: string, params?: object) =>
    http.request<T>("get", `/api/v1${path}`, { params }),
  post: <T>(path: string, data: unknown) =>
    http.request<T>("post", `/api/v1${path}`, { data }),
  patch: <T>(path: string, data: unknown) =>
    http.request<T>("patch", `/api/v1${path}`, { data })
};

export const applicationStatuses = [
  ["pending", "待评估"],
  ["to_contact", "待建联"],
  ["contacting", "沟通中"],
  ["submitted", "已推荐"],
  ["interview", "面试中"],
  ["offer", "Offer"],
  ["hired", "入职"],
  ["hold", "暂不推进"]
];
export const jobStatuses = [
  ["draft", "草稿"],
  ["open", "招聘中"],
  ["paused", "暂停"],
  ["closed", "关闭"]
];
export const dateTime = (value: string | null) =>
  value
    ? new Intl.DateTimeFormat("zh-CN", {
        timeZone: "Asia/Shanghai",
        dateStyle: "medium",
        timeStyle: "short"
      }).format(new Date(/Z$|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`))
    : "时间未记录";
export const messageOf = (error: unknown) =>
  error instanceof Error ? error.message : "操作失败，请重试";
