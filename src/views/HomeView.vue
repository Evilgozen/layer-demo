<script setup>
import AIAssistant from '../components/AIAssistant.vue'
import { useUserStore } from '../stores/userStore'

const userStore = useUserStore()
</script>

<template>
  <div class="home-container">
    <a-layout>
      <a-layout-header class="header">
        <div class="logo">理工包青天 - 法律援助助手</div>
        <div class="user-info">
          <span v-if="userStore.user">欢迎，{{ userStore.user.username }}</span>
          <a-button type="link" @click="userStore.logout()">退出登录</a-button>
        </div>
      </a-layout-header>
      <a-layout-content class="content">
        <AIAssistant />
      </a-layout-content>
      <a-layout-footer class="footer">
        © 2025 理工包青天 - 法律援助助手
      </a-layout-footer>
    </a-layout>
  </div>
</template>

<style scoped>
.home-container {
  height: 100vh;
  width: 100%;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #001529;
  color: white;
  padding: 0 24px;
}

.logo {
  font-size: 18px;
  font-weight: bold;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.content {
  padding: 24px;
  background: #f0f2f5;
  min-height: calc(100vh - 134px);
}

.footer {
  text-align: center;
  background: #f0f2f5;
  color: rgba(0, 0, 0, 0.65);
}
</style>
