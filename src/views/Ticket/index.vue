<template>
  <div class="ticket-container">
    <div class="page-header">
      <h2>工单管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建工单
      </el-button>
    </div>

    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="工单状态" clearable @change="loadTickets">
        <el-option label="全部" value="" />
        <el-option label="待处理" value="open" />
        <el-option label="处理中" value="processing" />
        <el-option label="已关闭" value="closed" />
      </el-select>
    </div>

    <el-table :data="tickets" v-loading="loading" stripe>
      <el-table-column prop="ticket_no" label="工单号" width="180" />
      <el-table-column prop="type" label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="getTypeColor(row.type)">
            {{ getTypeText(row.type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="assigned_to" label="处理人" width="100">
        <template #default="{ row }">
          {{ row.assigned_to || '未分配' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewTicket(row)">查看</el-button>
          <el-button size="small" type="danger" @click="deleteTicket(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadTickets"
      />
    </div>

    <!-- 创建工单对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建工单" width="600px">
      <el-form :model="ticketForm" :rules="ticketRules" ref="ticketFormRef" label-width="100px">
        <el-form-item label="工单类型" prop="type">
          <el-select v-model="ticketForm.type" placeholder="请选择类型">
            <el-option label="投诉" value="complaint" />
            <el-option label="退货" value="return" />
            <el-option label="换货" value="exchange" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="ticketForm.title" />
        </el-form-item>
        <el-form-item label="问题描述" prop="description">
          <el-input v-model="ticketForm.description" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTicket">确定</el-button>
      </template>
    </el-dialog>

    <!-- 工单详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="工单详情" width="600px">
      <el-descriptions :column="2" border v-if="currentTicket">
        <el-descriptions-item label="工单号">{{ currentTicket.ticket_no }}</el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="getTypeColor(currentTicket.type)">
            {{ getTypeText(currentTicket.type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentTicket.status)">
            {{ getStatusText(currentTicket.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="处理人">{{
          currentTicket.assigned_to || '未分配'
        }}</el-descriptions-item>
        <el-descriptions-item label="标题" :span="2">{{
          currentTicket.title
        }}</el-descriptions-item>
        <el-descriptions-item label="问题描述" :span="2">{{
          currentTicket.description
        }}</el-descriptions-item>
        <el-descriptions-item label="处理结果" :span="2">{{
          currentTicket.resolution || '暂无'
        }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{
          formatDateTime(currentTicket.created_at)
        }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{
          formatDateTime(currentTicket.updated_at)
        }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ticketApi } from '../../services/api'
import { TicketResponse, TicketCreate } from '../../services/types'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const tickets = ref<TicketResponse[]>([])
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const currentTicket = ref<TicketResponse | null>(null)
const ticketFormRef = ref<FormInstance>()

const ticketForm = reactive({
  type: '' as 'complaint' | 'return' | 'exchange' | 'other',
  title: '',
  description: '',
})

const ticketRules: FormRules = {
  type: [{ required: true, message: '请选择工单类型', trigger: 'change' }],
  description: [{ required: true, message: '请输入问题描述', trigger: 'blur' }],
}

const loadTickets = async () => {
  loading.value = true
  try {
    const response = await ticketApi.list({
      status: statusFilter.value || null,
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
    })
    tickets.value = response.data
    total.value = response.data.length
  } catch (error) {
    ElMessage.error('加载工单失败')
  } finally {
    loading.value = false
  }
}

const createTicket = async () => {
  if (!ticketFormRef.value) return

  await ticketFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const ticketNo = 'TKT' + Date.now()
        const data: TicketCreate = {
          ticket_no: ticketNo,
          user_id: authStore.currentUser!.id,
          type: ticketForm.type,
          title: ticketForm.title || null,
          description: ticketForm.description,
        }
        await ticketApi.create(data)
        ElMessage.success('工单创建成功')
        showCreateDialog.value = false
        loadTickets()
      } catch (error) {
        ElMessage.error('创建工单失败')
      }
    }
  })
}

const viewTicket = (ticket: TicketResponse) => {
  currentTicket.value = ticket
  showDetailDialog.value = true
}

const deleteTicket = async (ticket: TicketResponse) => {
  try {
    await ElMessageBox.confirm('确定要删除这个工单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await ticketApi.delete(ticket.id)
    ElMessage.success('删除成功')
    loadTickets()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    complaint: 'danger',
    return: 'warning',
    exchange: 'primary',
    other: 'info',
  }
  return colors[type] || 'info'
}

const getTypeText = (type: string) => {
  const texts: Record<string, string> = {
    complaint: '投诉',
    return: '退货',
    exchange: '换货',
    other: '其他',
  }
  return texts[type] || type
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    open: 'warning',
    processing: 'primary',
    closed: 'info',
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    open: '待处理',
    processing: '处理中',
    closed: '已关闭',
  }
  return texts[status] || status
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadTickets()
})
</script>

<style scoped>
.ticket-container {
  padding: 20px;
  background: white;
  border-radius: 8px;
  min-height: calc(100vh - 140px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.filter-bar {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
