import { defineStore } from 'pinia'
import { userApi } from '../services/api'
import { UserResponse } from '../services/types'
import { storage } from '../utils/storage'

interface AuthState {
  user: UserResponse | null
  token: string | null
  loading: boolean
  error: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: storage.getUser(),
    token: storage.getToken(),
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    currentUser: (state) => state.user,
  },

  actions: {
    async register(username: string, nickname: string, password: string) {
      this.loading = true
      this.error = null
      try {
        const response = await userApi.register({ username, nickname, password })
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.message || '注册失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async login(username: string, password: string) {
      this.loading = true
      this.error = null
      try {
        const response = await userApi.login({ username, password })
        const { access_token } = response.data
        this.token = access_token
        storage.setToken(access_token)

        // 获取用户信息
        const userResponse = await userApi.getCurrentUser()
        this.user = userResponse.data
        storage.setUser(userResponse.data)

        return userResponse.data
      } catch (error: any) {
        this.error = error.response?.data?.message || '登录失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async logout() {
      this.token = null
      this.user = null
      storage.clear()
    },

    async getCurrentUser() {
      if (!this.token) return
      this.loading = true
      try {
        const response = await userApi.getCurrentUser()
        this.user = response.data
        storage.setUser(response.data)
        return response.data
      } catch (error) {
        this.logout()
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateProfile(nickname: string) {
      this.loading = true
      try {
        const response = await userApi.updateProfile({ nickname })
        this.user = response.data
        storage.setUser(response.data)
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.message || '更新失败'
        throw error
      } finally {
        this.loading = false
      }
    },
  },
})
