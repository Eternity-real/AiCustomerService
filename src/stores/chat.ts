import { defineStore } from 'pinia'
import { chatApi } from '../services/api'
import {
  ChatRequest,
  ChatResponse,
  MessageResponse,
  HistoryRequest,
  SessionResponse,
  SessionListItem,
} from '../services/types'

interface ChatState {
  sessions: SessionListItem[]
  currentSession: SessionResponse | null
  messages: MessageResponse[]
  loading: boolean
  error: string | null
  sending: boolean
}

export const useChatStore = defineStore('chat', {
  state: (): ChatState => ({
    sessions: [],
    currentSession: null,
    messages: [],
    loading: false,
    error: null,
    sending: false,
  }),

  actions: {
    async loadSessions() {
      this.loading = true
      try {
        const response = await chatApi.listSessions()
        this.sessions = response.data
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.message || '加载会话失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async loadSessionDetail(sessionId: number) {
      this.loading = true
      try {
        const response = await chatApi.getSession(sessionId)
        this.currentSession = response.data
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.message || '加载会话详情失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async loadMessages(sessionId: number, limit: number = 50, before: number | null = null) {
      this.loading = true
      try {
        const response = await chatApi.getHistory({ session_id: sessionId, limit, before })
        this.messages = response.data
        return response.data
      } catch (error: any) {
        this.error = error.response?.data?.message || '加载消息失败'
        throw error
      } finally {
        this.loading = false
      }
    },

    async sendMessage(sessionId: number | null, content: string) {
      this.sending = true
      this.error = null
      try {
        const response = await chatApi.send({ session_id: sessionId, content })
        const chatResponse = response.data

        // 如果是新会话，更新当前会话
        if (!sessionId) {
          await this.loadSessionDetail(chatResponse.session_id)
        }

        // 添加新消息到列表
        this.messages.push(chatResponse.message)

        // 重新加载会话列表
        await this.loadSessions()

        return chatResponse
      } catch (error: any) {
        this.error = error.response?.data?.message || '发送消息失败'
        throw error
      } finally {
        this.sending = false
      }
    },

    async deleteSession(sessionId: number) {
      this.loading = true
      try {
        await chatApi.deleteSession(sessionId)
        // 从列表中移除
        this.sessions = this.sessions.filter((s) => s.id !== sessionId)
        // 如果是当前会话，清空
        if (this.currentSession?.id === sessionId) {
          this.currentSession = null
          this.messages = []
        }
      } catch (error: any) {
        this.error = error.response?.data?.message || '删除会话失败'
        throw error
      } finally {
        this.loading = false
      }
    },
  },
})
