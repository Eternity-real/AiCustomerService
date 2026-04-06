// API 响应类型
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

// 用户相关
export interface UserCreate {
  username: string
  nickname: string
  password: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface UserResponse {
  id: number
  username: string
  nickname: string
  created_at: string
  updated_at: string
}

export interface UserUpdate {
  nickname: string
}

// 订单相关
export interface OrderItemInput {
  name: string
  quantity: number
  price: number | string
}

export interface OrderItemOutput {
  name: string
  quantity: number
  price: string
}

export interface OrderCreate {
  user_id: number
  items: OrderItemInput[]
  total_amount: number | string
  status?: string
  receiver_name: string
  receiver_phone: string
  shipping_address: string
  remark?: string | null
  order_no: string
}

export interface OrderUpdate {
  status?: string | null
  receiver_name?: string | null
  receiver_phone?: string | null
  shipping_address?: string | null
  remark?: string | null
}

export interface OrderResponse {
  id: number
  user_id: number
  order_no: string
  items: OrderItemOutput[]
  total_amount: string
  status: string
  receiver_name: string
  receiver_phone: string
  shipping_address: string
  remark: string | null
  created_at: string
  updated_at: string
}

// 工单相关
export interface TicketCreate {
  ticket_no: string
  user_id: number
  order_id?: number | null
  session_id?: number | null
  type: 'complaint' | 'return' | 'exchange' | 'other'
  title?: string | null
  description: string
  status?: 'open' | 'processing' | 'closed'
  assigned_to?: string | null
  resolution?: string | null
}

export interface TicketUpdate {
  status?: 'open' | 'processing' | 'closed' | null
  assigned_to?: string | null
  resolution?: string | null
}

export interface TicketResponse {
  id: number
  user_id: number
  ticket_no: string
  order_id: number | null
  session_id: number | null
  type: string
  title: string | null
  description: string
  status: string
  assigned_to: string | null
  resolution: string | null
  created_at: string
  updated_at: string
}

// 聊天相关
export interface ChatRequest {
  session_id?: number | null
  content: string
}

export interface MessageResponse {
  id: number
  session_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  meta_data?: Record<string, any> | null
  created_at: string
  updated_at: string
}

export interface ChatResponse {
  session_id: number
  message: MessageResponse
}

export interface HistoryRequest {
  session_id: number
  limit?: number
  before?: number | null
}

export interface SessionResponse {
  id: number
  user_id: number | null
  session_uuid: string
  title: string | null
  status: 'active' | 'closed'
  started_at: string
  ended_at: string | null
  last_message_at: string
}

export interface SessionListItem {
  id: number
  session_uuid: string
  title: string | null
  status: string
  last_message_at: string
  message_count: number | null
}

export interface SessionUpdate {
  title?: string | null
  status?: 'active' | 'closed' | null
  ended_at?: string | null
}

// 订单状态类型
export type OrderStatus = 'pending' | 'paid' | 'shipped' | 'completed' | 'cancelled'

// 工单状态类型
export type TicketStatus = 'open' | 'processing' | 'closed'

// 工单类型
export type TicketType = 'complaint' | 'return' | 'exchange' | 'other'
