import axios from "axios";

export type UserResult = {
  success: boolean;
  data: {
    avatar: string;
    username: string;
    nickname: string;
    roles: string[];
    permissions: string[];
    accessToken: string;
    refreshToken: string;
    expires: Date;
  };
};
export type RefreshTokenResult = UserResult;
interface SessionResult {
  access_token: string;
  expires_at: string;
  user: { username: string; display_name: string; role: string };
}
const sessionHttp = axios.create({
  timeout: 10000,
  headers: { "X-Hunter-Client": "web" }
});
function adapt(value: SessionResult): UserResult {
  return {
    success: true,
    data: {
      avatar: "",
      username: value.user.username,
      nickname: value.user.display_name,
      roles: [value.user.role],
      permissions: ["*:*:*"],
      accessToken: value.access_token,
      refreshToken: "",
      expires: new Date(
        value.expires_at.endsWith("Z") ||
        /[+-]\d\d:\d\d$/.test(value.expires_at)
          ? value.expires_at
          : `${value.expires_at}Z`
      )
    }
  };
}
export async function getLogin(data?: object) {
  return adapt(
    (await sessionHttp.post<SessionResult>("/api/v1/auth/login", data)).data
  );
}
export async function refreshTokenApi(_data?: object) {
  return adapt(
    (await sessionHttp.post<SessionResult>("/api/v1/auth/refresh")).data
  );
}
export const logoutApi = () => sessionHttp.post("/api/v1/auth/logout");
