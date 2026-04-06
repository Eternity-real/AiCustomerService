<template>
  <div class="sidebar">
    <el-menu :default-active="activeMenu" class="sidebar-menu" router :unique-opened="true">
      <el-menu-item index="/chat">
        <el-icon><ChatLineRound /></el-icon>
        <span>智能客服</span>
      </el-menu-item>

      <el-menu-item index="/orders">
        <el-icon><ShoppingCart /></el-icon>
        <span>订单管理</span>
      </el-menu-item>

      <el-menu-item index="/tickets">
        <el-icon><Document /></el-icon>
        <span>工单管理</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { ChatLineRound, ShoppingCart, Document } from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => {
  return route.path
})
</script>

<style scoped>
.sidebar {
  height: 100%;
  padding-top: 20px;
}

.sidebar-menu {
  border-right: none;
}

:deep(.el-menu-item.is-active) {
  background-color: #ecf5ff !important;
  color: #409eff !important;
}
</style>
