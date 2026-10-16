import Axios, { type AxiosError, type AxiosRequestConfig } from "axios";
import { getToken, setToken, removeToken, formatToken } from "@/utils/auth";
import { refreshTokenApi } from "@/api/user";

let refreshing: Promise<void> | null = null;
export function refreshSession(): Promise<void> {
  if (!refreshing) {
    refreshing = refreshTokenApi()
      .then(result => {
        setToken(result.data);
      })
      .catch(error => {
        removeToken();
        throw error;
      })
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}
const client = Axios.create({ timeout: 10000 });
client.interceptors.request.use(async config => {
  if (getToken()?.expires <= Date.now()) await refreshSession();
  const token = getToken()?.accessToken;
  if (token) config.headers.Authorization = formatToken(token);
  return config;
});
client.interceptors.response.use(
  response => response.data,
  async (
    error: AxiosError<{
      message?: string;
      details?: { field: string; message: string }[];
    }>
  ) => {
    const config = error.config as AxiosRequestConfig & {
      hunterRetried?: boolean;
    };
    if (error.response?.status === 401 && config && !config.hunterRetried) {
      config.hunterRetried = true;
      try {
        await refreshSession();
        return await client.request(config);
      } catch {
        removeToken();
        const { router } = await import("@/router");
        void router.push("/login");
      }
    }
    const data = error.response?.data;
    const details = data?.details
      ?.map(item => `${item.field}: ${item.message}`)
      .join("；");
    return Promise.reject(
      new Error(
        details ||
          data?.message ||
          (error.response
            ? "服务暂时不可用，请重试"
            : "无法连接服务，请检查后端是否启动")
      )
    );
  }
);
class PureHttp {
  request<T>(
    method: string,
    url: string,
    param?: AxiosRequestConfig,
    config?: AxiosRequestConfig
  ): Promise<T> {
    return client.request<T, T>({ method, url, ...param, ...config });
  }
  post<T, P>(
    url: string,
    params?: AxiosRequestConfig<P>,
    config?: AxiosRequestConfig
  ): Promise<T> {
    return this.request<T>("post", url, params, config);
  }
  get<T, P>(
    url: string,
    params?: AxiosRequestConfig<P>,
    config?: AxiosRequestConfig
  ): Promise<T> {
    return this.request<T>("get", url, params, config);
  }
}
export const http = new PureHttp();
