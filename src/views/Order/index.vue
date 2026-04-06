<template>
  <div class="order-container">
    <div class="page-header">
      <h2>订单管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建订单
      </el-button>
    </div>

    <div class="filter-bar">
      <el-select v-model="statusFilter" placeholder="订单状态" clearable @change="loadOrders">
        <el-option label="全部" value="" />
        <el-option label="待支付" value="pending" />
        <el-option label="已支付" value="paid" />
        <el-option label="已发货" value="shipped" />
        <el-option label="已完成" value="completed" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
    </div>

    <el-table :data="orders" v-loading="loading" stripe>
      <el-table-column prop="order_no" label="订单号" width="180" />
      <el-table-column label="商品" min-width="200">
        <template #default="{ row }">
          <div v-for="item in row.items" :key="item.name" class="order-item">
            {{ item.name }} x {{ item.quantity }}
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="total_amount" label="总金额" width="120">
        <template #default="{ row }"> ¥{{ row.total_amount }} </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="receiver_name" label="收货人" width="100" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewOrder(row)">查看</el-button>
          <el-button size="small" type="primary" @click="editOrder(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteOrder(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadOrders"
      />
    </div>

    <!-- 创建订单对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建订单" width="600px">
      <el-form :model="orderForm" :rules="orderRules" ref="orderFormRef" label-width="100px">
        <el-form-item label="收货人" prop="receiver_name">
          <el-input v-model="orderForm.receiver_name" />
        </el-form-item>
        <el-form-item label="联系电话" prop="receiver_phone">
          <el-input v-model="orderForm.receiver_phone" />
        </el-form-item>
        <el-form-item label="收货地址" prop="shipping_address">
          <el-input v-model="orderForm.shipping_address" type="textarea" />
        </el-form-item>
        <el-form-item label="订单备注">
          <el-input v-model="orderForm.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createOrder">确定</el-button>
      </template>
    </el-dialog>

    <!-- 订单详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="订单详情" width="600px">
      <el-descriptions :column="2" border v-if="currentOrder">
        <el-descriptions-item label="订单号">{{ currentOrder.order_no }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentOrder.status)">
            {{ getStatusText(currentOrder.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="收货人">{{ currentOrder.receiver_name }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{
          currentOrder.receiver_phone
        }}</el-descriptions-item>
        <el-descriptions-item label="收货地址" :span="2">{{
          currentOrder.shipping_address
        }}</el-descriptions-item>
        <el-descriptions-item label="订单备注" :span="2">{{
          currentOrder.remark || '无'
        }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{
          formatDateTime(currentOrder.created_at)
        }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{
          formatDateTime(currentOrder.updated_at)
        }}</el-descriptions-item>
      </el-descriptions>
      <div class="order-items-detail">
        <h4>商品列表</h4>
        <el-table :data="currentOrder?.items" stripe size="small">
          <el-table-column prop="name" label="商品名称" />
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="price" label="单价" width="120">
            <template #default="{ row }"> ¥{{ row.price }} </template>
          </el-table-column>
        </el-table>
        <div class="total-amount">
          总金额：<span class="amount">¥{{ currentOrder?.total_amount }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { orderApi } from '../../services/api'
import { OrderResponse, OrderCreate } from '../../services/types'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const loading = ref(false)
const orders = ref<OrderResponse[]>([])
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(100)
const total = ref(0)

const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const currentOrder = ref<OrderResponse | null>(null)
const orderFormRef = ref(null) as any

const orderForm = reactive({
  receiver_name: '',
  receiver_phone: '',
  shipping_address: '',
  remark: '',
})

const orderRules: FormRules = {
  receiver_name: [{ required: true, message: '请输入收货人姓名', trigger: 'blur' }],
  receiver_phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }],
  shipping_address: [{ required: true, message: '请输入收货地址', trigger: 'blur' }],
}

const loadOrders = async () => {
  loading.value = true
  try {
    const response = await orderApi.list({
      status: statusFilter.value || null,
      skip: 0,
      limit: 100,
    })
    orders.value = response.data
    total.value = response.data.length
  } catch (error: any) {
    console.error('加载订单错误:', error)
    ElMessage.error(
      '加载订单失败：' + (error.response?.data?.message || error.message || '未知错误'),
    )
  } finally {
    loading.value = false
  }
}

const createOrder = async () => {
  if (!orderFormRef.value) return

  await orderFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      try {
        const orderNo = 'ORD' + Date.now()
        const data: OrderCreate = {
          user_id: authStore.currentUser!.id,
          items: [{ name: '示例商品', quantity: 1, price: 99.99 }],
          total_amount: 99.99,
          order_no: orderNo,
          receiver_name: orderForm.receiver_name,
          receiver_phone: orderForm.receiver_phone,
          shipping_address: orderForm.shipping_address,
          remark: orderForm.remark || null,
        }
        await orderApi.create(data)
        ElMessage.success('订单创建成功')
        showCreateDialog.value = false
        loadOrders()
        // 清空表单
        orderForm.receiver_name = ''
        orderForm.receiver_phone = ''
        orderForm.shipping_address = ''
        orderForm.remark = ''
      } catch (error: any) {
        ElMessage.error('创建订单失败：' + (error.response?.data?.message || ''))
      }
    }
  })
}

const viewOrder = async (order: OrderResponse) => {
  try {
    const response = await orderApi.get(order.order_no)
    currentOrder.value = response.data
    showDetailDialog.value = true
  } catch (error: any) {
    ElMessage.error('加载订单详情失败：' + (error.response?.data?.message || ''))
  }
}

const editOrder = (order: OrderResponse) => {
  ElMessage.info('编辑功能开发中')
}

const deleteOrder = async (order: OrderResponse) => {
  try {
    await ElMessageBox.confirm('确定要删除这个订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await orderApi.delete(order.order_no)
    ElMessage.success('删除成功')
    loadOrders()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + (error.response?.data?.message || ''))
    }
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'warning',
    paid: 'primary',
    shipped: 'info',
    completed: 'success',
    cancelled: 'danger',
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    shipped: '已发货',
    completed: '已完成',
    cancelled: '已取消',
  }
  return texts[status] || status
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.order-container {
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

.order-item {
  font-size: 13px;
  line-height: 1.8;
}

.order-items-detail {
  margin-top: 20px;
}

.order-items-detail h4 {
  margin-bottom: 10px;
  color: #303133;
}

.total-amount {
  text-align: right;
  margin-top: 10px;
  font-size: 16px;
}

.total-amount .amount {
  color: #f56c6c;
  font-weight: bold;
  font-size: 20px;
}
</style>
