import { defineStore } from "pinia";
import {
  type userType,
  store,
  router,
  resetRouter,
  routerArrays,
  storageLocal
} from "../utils";
import { getLogin, logoutApi } from "@/api/user";
import { refreshSession } from "@/utils/http";
import { useMultiTagsStoreHook } from "./multiTags";
import {
  type DataInfo,
  setToken,
  removeToken,
  userKey,
  getToken
} from "@/utils/auth";

export const useUserStore = defineStore("pure-user", {
  state: (): userType => ({
    avatar: "",
    username: "",
    nickname: "",
    roles: [],
    permissions: [],
    isRemembered: false,
    loginDay: 7
  }),
  actions: {
    SET_AVATAR(value: string) {
      this.avatar = value;
    },
    SET_USERNAME(value: string) {
      this.username = value;
    },
    SET_NICKNAME(value: string) {
      this.nickname = value;
    },
    SET_ROLES(value: string[]) {
      this.roles = value;
    },
    SET_PERMS(value: string[]) {
      this.permissions = value;
    },
    SET_ISREMEMBERED(value: boolean) {
      this.isRemembered = value;
    },
    SET_LOGINDAY(value: number) {
      this.loginDay = value;
    },
    async loginByUsername(data: { username: string; password: string }) {
      const result = await getLogin(data);
      setToken(result.data);
      return result;
    },
    async restoreSession() {
      if (getToken()) return true;
      try {
        await refreshSession();
        return true;
      } catch {
        return false;
      }
    },
    async logOut() {
      // Revocation must succeed before reporting a completed logout.
      await logoutApi();
      this.username = "";
      this.roles = [];
      this.permissions = [];
      removeToken();
      useMultiTagsStoreHook().handleTags("equal", [...routerArrays]);
      resetRouter();
      await router.push("/login");
    },
    async handRefreshToken(_data?: object) {
      await refreshSession();
      const profile = storageLocal().getItem<DataInfo<number>>(userKey);
      return { success: true, data: { ...profile, ...getToken() } };
    }
  }
});
export function useUserStoreHook() {
  return useUserStore(store);
}
