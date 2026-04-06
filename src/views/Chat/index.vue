<template>
  <div class="chat-container">
    <el-row :gutter="20">
      <!-- 会话列表 -->
      <el-col :span="6">
        <SessionList
          :sessions="sessions"
          :loading="loading"
          :current-session-id="currentSession?.id"
          @select-session="selectSession"
          @delete-session="deleteSession"
        />
      </el-col>

      <!-- 聊天界面 -->
      <el-col :span="18">
        <div class="chat-main">
          <div v-if="!currentSession" class="empty-chat">
            <el-empty description="请选择一个会话或开始新对话" />
          </div>

          <div v-else class="chat-content">
            <!-- 消息历史 -->
            <ChatHistory :messages="messages" :loading="loading" @load-more="loadMoreMessages" />

            <!-- 输入框 -->
            <ChatInput :sending="sending" @send-message="sendMessage" />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useChatStore } from '../../stores/chat'
import SessionList from '../../components/Chat/SessionList.vue'
import ChatHistory from '../../components/Chat/ChatHistory.vue'
import ChatInput from '../../components/Chat/ChatInput.vue'

const chatStore = useChatStore()

const sessions = computed(() => chatStore.sessions)
const currentSession = computed(() => chatStore.currentSession)
const messages = computed(() => chatStore.messages)
const loading = computed(() => chatStore.loading)
const sending = computed(() => chatStore.sending)

// 加载会话列表
onMounted(async () => {
  await chatStore.loadSessions()
})

// 选择会话
const selectSession = async (sessionId: number) => {
  await chatStore.loadSessionDetail(sessionId)
  await chatStore.loadMessages(sessionId)
}

// 发送消息
const sendMessage = async (content: string) => {
  if (!content.trim()) return

  await chatStore.sendMessage(currentSession.value?.id || null, content)
}

// 加载更多消息
const loadMoreMessages = async () => {
  if (!currentSession.value || messages.value.length === 0) return

  const firstMessage = messages.value[messages.value.length - 1]
  await chatStore.loadMessages(currentSession.value.id, 20, firstMessage.id)
}

// 删除会话
const deleteSession = async (sessionId: number) => {
  await chatStore.deleteSession(sessionId)
}
</script>

<style scoped>
.chat-container {
  height: calc(100vh - 100px);
}

.chat-main {
  height: 100%;
  border-radius: 8px;
  background: white;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.empty-chat {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
