<template>
  <div class="app">
    <el-container style="height: 100vh">
      <!-- 导航栏 -->
      <el-header height="60px" class="header">
        <Navbar />
      </el-header>

      <!-- 主内容区 -->
      <el-container>
        <!-- 侧边栏 -->
        <el-aside width="200px" class="sidebar">
          <Sidebar />
        </el-aside>

        <!-- 内容区 -->
        <el-main class="main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import Navbar from './components/common/Navbar.vue'
import Sidebar from './components/common/Sidebar.vue'
</script>

<style scoped>
.app {
  height: 100vh;
  overflow: hidden;
}

.header {
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sidebar {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.main {
  padding: 20px;
  overflow-y: auto;
  background: #f0f2f5;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
