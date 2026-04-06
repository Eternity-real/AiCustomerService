<template>
  <div class="navbar">
    <div class="logo">
      <el-icon><ChatDotRound /></el-icon>
      <span>智能客服系统</span>
    </div>

    <div class="user-info" v-if="isAuthenticated">
      <el-dropdown trigger="click">
        <span class="user-name">{{ currentUser?.nickname || '用户' }}</span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="goToProfile">
              <el-icon><UserFilled /></el-icon>
              <span>个人资料</span>
            </el-dropdown-item>
            <el-dropdown-item @click="logout">
              <el-icon><SwitchButton /></el-icon>
              <span>退出登录</span>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { ChatDotRound, UserFilled, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const currentUser = computed(() => authStore.currentUser)

const goToProfile = () => {
  router.push('/profile')
}

const logout = async () => {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.logo {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
}

.logo span {
  margin-left: 10px;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-name {
  cursor: pointer;
  color: white;
  font-size: 14px;
}

:deep(.el-dropdown-menu__item) {
  min-width: 120px;
}
</style>
