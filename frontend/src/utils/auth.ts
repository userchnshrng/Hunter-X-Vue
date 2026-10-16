import Cookies from "js-cookie";
import { useUserStoreHook } from "@/store/modules/user";
import { storageLocal, isString, isIncludeAllChildren } from "@pureadmin/utils";

export interface DataInfo<T> {
  accessToken: string;
  expires: T;
  refreshToken?: string;
  avatar?: string;
  username?: string;
  nickname?: string;
  roles?: string[];
  permissions?: string[];
}
export const userKey = "hunter-user-profile";
export const TokenKey = "hunter-access-memory";
export const multipleTabsKey = "hunter-session-present";
let session: DataInfo<number> | undefined;
export function getToken(): DataInfo<number> | undefined {
  return session;
}
export function setToken(data: DataInfo<Date>) {
  session = {
    ...data,
    expires: new Date(data.expires).getTime(),
    refreshToken: undefined
  };
  const profile = {
    avatar: data.avatar || "",
    username: data.username || "",
    nickname: data.nickname || "",
    roles: data.roles || [],
    permissions: data.permissions || []
  };
  storageLocal().setItem(userKey, profile);
  const store = useUserStoreHook();
  store.SET_AVATAR(profile.avatar);
  store.SET_USERNAME(profile.username);
  store.SET_NICKNAME(profile.nickname);
  store.SET_ROLES(profile.roles);
  store.SET_PERMS(profile.permissions);
}
export function removeToken() {
  session = undefined;
  Cookies.remove(TokenKey);
  Cookies.remove(multipleTabsKey);
  storageLocal().removeItem(userKey);
}
export const formatToken = (token: string) => `Bearer ${token}`;
export function hasPerms(value: string | string[]): boolean {
  const permissions = useUserStoreHook().permissions || [];
  return (
    permissions.includes("*:*:*") ||
    (isString(value)
      ? permissions.includes(value)
      : isIncludeAllChildren(value, permissions))
  );
}
