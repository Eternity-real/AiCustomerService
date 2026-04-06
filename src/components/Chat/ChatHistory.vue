<template>
  <div class="chat-history" ref="historyRef">
    <div class="load-more" v-if="hasMore && !loading">
      <el-button text @click="$emit('load-more')">加载更多消息</el-button>
    </div>
    <div class="loading" v-if="loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    <div class="message-list">
      <div v-for="msg in reversedMessages" :key="msg.id" :class="['message-item', msg.role]">
        <div class="message-avatar">
          <el-avatar :size="36" v-if="msg.role === 'user'">
            {{ userInitial }}
          </el-avatar>
          <el-avatar :size="36" v-else style="background: #409eff">
            <el-icon><Service /></el-icon>
          </el-avatar>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="role-name">{{ msg.role === 'user' ? '我' : '智能客服' }}</span>
            <span class="message-time">{{ formatTime(msg.created_at) }}</span>
          </div>
          <div class="message-text" v-html="formatMessage(msg.content)"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, nextTick, watch } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { MessageResponse } from '../../services/types'
import { Loading, Service } from '@element-plus/icons-vue'

const props = defineProps<{
  messages: MessageResponse[]
  loading: boolean
}>()

defineEmits<{
  (e: 'load-more'): void
}>()

const authStore = useAuthStore()
const historyRef = ref<HTMLElement>()

const userInitial = computed(() => {
  return authStore.currentUser?.nickname?.charAt(0).toUpperCase() || 'U'
})

const reversedMessages = computed(() => {
  return [...props.messages].reverse()
})

const hasMore = ref(true)

watch(
  () => props.messages,
  () => {
    nextTick(() => {
      scrollToBottom()
    })
  },
  { deep: true },
)

const scrollToBottom = () => {
  if (historyRef.value) {
    historyRef.value.scrollTop = historyRef.value.scrollHeight
  }
}

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`

  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const formatMessage = (content: string) => {
  return content.replace(/\n/g, '<br>')
}
</script>

<style scoped>
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
}

.load-more {
  text-align: center;
  padding: 10px 0;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #909399;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-item.user .message-content {
  align-items: flex-end;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #909399;
}

.message-text {
  padding: 12px 16px;
  border-radius: 8px;
  background: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  line-height: 1.6;
  word-break: break-word;
}

.message-item.user .message-text {
  background: #409eff;
  color: white;
}

.message-item.assistant .message-text {
  background: white;
}

.role-name {
  font-weight: 500;
}

.message-time {
  font-size: 11px;
}
</style>
