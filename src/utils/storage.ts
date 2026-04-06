const TOKEN_KEY = 'auth_token'
const USER_KEY = 'user_info'

export const storage = {
  // Token 相关
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },
  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  },
  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY)
  },

  // 用户信息相关
  getUser(): any | null {
    const userStr = localStorage.getItem(USER_KEY)
    return userStr ? JSON.parse(userStr) : null
  },
  setUser(user: any): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  removeUser(): void {
    localStorage.removeItem(USER_KEY)
  },

  // 清空所有
  clear(): void {
    localStorage.clear()
  },
}
