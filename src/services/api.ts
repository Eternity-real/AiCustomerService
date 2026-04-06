import axios from '../utils/axios'
import {
  UserCreate,
  UserLogin,
  UserResponse,
  UserUpdate,
  OrderCreate,
  OrderUpdate,
  OrderResponse,
  TicketCreate,
  TicketUpdate,
  TicketResponse,
  ChatRequest,
  ChatResponse,
  HistoryRequest,
  SessionResponse,
  SessionUpdate,
  SessionListItem,
  MessageResponse,
  ApiResponse,
} from './types'

// 用户相关
export const userApi = {
  register: async (data: UserCreate): Promise<ApiResponse<UserResponse>> => {
    return (await axios.post('/api/users/register', data)).data
  },
  login: async (
    data: UserLogin,
  ): Promise<ApiResponse<{ access_token: string; token_type: string }>> => {
    return (await axios.post('/api/users/login', data)).data
  },
  getCurrentUser: async (): Promise<ApiResponse<UserResponse>> => {
    return (await axios.get('/api/users/me')).data
  },
  updateProfile: async (data: UserUpdate): Promise<ApiResponse<UserResponse>> => {
    return (await axios.put('/api/users/me', data)).data
  },
}

// 订单相关
export const orderApi = {
  create: async (data: OrderCreate): Promise<ApiResponse<OrderResponse>> => {
    return (await axios.post('/api/orders/', data)).data
  },
  list: async (params?: {
    status?: string | null
    skip?: number
    limit?: number
  }): Promise<ApiResponse<OrderResponse[]>> => {
    return (await axios.get('/api/orders/', { params })).data
  },
  // 根据订单号查询订单详情
  get: async (orderNo: string): Promise<ApiResponse<OrderResponse>> => {
    return (await axios.get(`/api/orders/order-no/${orderNo}`)).data
  },
  // 根据订单号更新订单
  update: async (orderNo: string, data: OrderUpdate): Promise<ApiResponse<OrderResponse>> => {
    return (await axios.put(`/api/orders/order-no/${orderNo}`, data)).data
  },
  // 根据订单号删除订单
  delete: async (orderNo: string): Promise<ApiResponse<boolean>> => {
    return (await axios.delete(`/api/orders/order-no/${orderNo}`)).data
  },
}

// 工单相关
export const ticketApi = {
  create: async (data: TicketCreate): Promise<ApiResponse<TicketResponse>> => {
    return (await axios.post('/api/tickets/', data)).data
  },
  list: async (params?: {
    status?: string | null
    skip?: number
    limit?: number
  }): Promise<ApiResponse<TicketResponse[]>> => {
    return (await axios.get('/api/tickets/', { params })).data
  },
  get: async (ticketId: number): Promise<ApiResponse<TicketResponse>> => {
    return (await axios.get(`/api/tickets/${ticketId}`)).data
  },
  update: async (ticketId: number, data: TicketUpdate): Promise<ApiResponse<TicketResponse>> => {
    return (await axios.put(`/api/tickets/${ticketId}`, data)).data
  },
  delete: async (ticketId: number): Promise<ApiResponse<boolean>> => {
    return (await axios.delete(`/api/tickets/${ticketId}`)).data
  },
}

// 聊天相关
export const chatApi = {
  send: async (data: ChatRequest): Promise<ApiResponse<ChatResponse>> => {
    return (await axios.post('/api/chat/send', data)).data
  },
  getHistory: async (data: HistoryRequest): Promise<ApiResponse<MessageResponse[]>> => {
    return (await axios.post('/api/chat/history', data)).data
  },
  listSessions: async (params?: {
    skip?: number
    limit?: number
  }): Promise<ApiResponse<SessionListItem[]>> => {
    return (await axios.get('/api/sessions', { params })).data
  },
  getSession: async (sessionId: number): Promise<ApiResponse<SessionResponse>> => {
    return (await axios.get(`/api/sessions/${sessionId}`)).data
  },
  updateSession: async (
    sessionId: number,
    data: SessionUpdate,
  ): Promise<ApiResponse<SessionResponse>> => {
    return (await axios.put(`/api/sessions/${sessionId}`, data)).data
  },
  deleteSession: async (
    sessionId: number,
  ): Promise<ApiResponse<{ message: string; session_id: number }>> => {
    return (await axios.delete(`/api/sessions/${sessionId}`)).data
  },
}
