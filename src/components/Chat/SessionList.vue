<template>
  <div class="session-list">
    <div class="session-header">
      <h3>会话列表</h3>
      <el-button type="primary" size="small" @click="createNewSession"> 新对话 </el-button>
    </div>

    <div class="session-content" v-loading="loading">
      <div v-if="sessions.length === 0" class="empty-sessions">
        <el-empty description="暂无会话" :image-size="80" />
      </div>

      <div
        v-for="session in sessions"
        :key="session.id"
        :class="['session-item', { active: session.id === currentSessionId }]"
        @click="$emit('select-session', session.id)"
      >
        <div class="session-info">
          <div class="session-title">
            {{ session.title || '新对话' }}
          </div>
          <div class="session-time">
            {{ formatTime(session.last_message_at) }}
          </div>
        </div>
        <el-button type="danger" size="small" text @click.stop="handleDelete(session.id)">
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { SessionListItem } from '../../services/types'
import { Delete } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const props = defineProps<{
  sessions: SessionListItem[]
  loading: boolean
  currentSessionId?: number
}>()

const emit = defineEmits<{
  (e: 'select-session', sessionId: number): void
  (e: 'delete-session', sessionId: number): void
}>()

const createNewSession = () => {
  emit('select-session', 0)
}

const handleDelete = async (sessionId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个会话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    emit('delete-session', sessionId)
  } catch {
    // 用户取消
  }
}

const formatTime = (dateStr: string) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`

  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.session-list {
  height: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.session-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.session-content {
  flex: 1;
  overflow-y: auto;
}

.empty-sessions {
  padding: 40px 0;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.session-item:hover {
  background: #f5f7fa;
}

.session-item.active {
  background: #ecf5ff;
}

.session-info {
  flex: 1;
  overflow: hidden;
}

.session-title {
  font-size: 14px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
