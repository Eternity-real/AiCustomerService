<template>
  <div class="chat-input">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="3"
      placeholder="请输入您的问题，例如：查询我的订单、我想退货..."
      :disabled="sending"
      @keydown.enter.exact.prevent="handleSend"
    />
    <div class="input-actions">
      <div class="tips">
        <el-tag size="small" type="info">按 Enter 发送</el-tag>
      </div>
      <el-button type="primary" :loading="sending" @click="handleSend"> 发送 </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  sending: boolean
}>()

const emit = defineEmits<{
  (e: 'send-message', content: string): void
}>()

const inputText = ref('')

const handleSend = () => {
  const content = inputText.value.trim()
  if (content && !props.sending) {
    emit('send-message', content)
    inputText.value = ''
  }
}
</script>

<style scoped>
.chat-input {
  padding: 16px;
  background: white;
  border-top: 1px solid #e4e7ed;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.tips {
  color: #909399;
  font-size: 12px;
}
</style>
