<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { useUserStore } from './stores/userStore'
import { computed } from 'vue'

const userStore = useUserStore()
const isAuthenticated = computed(() => userStore.isAuthenticated)
</script>

<template>
  <div class="app-container">
    <!-- 导航菜单 -->
    <nav class="main-nav" v-if="isAuthenticated">
      <div class="nav-logo">
        <RouterLink to="/">法律助手</RouterLink>
      </div>
      <div class="nav-links">
        <RouterLink to="/" class="nav-link">AI助手</RouterLink>
        <RouterLink to="/legal-articles" class="nav-link">法条查询</RouterLink>
        <RouterLink to="/discussions" class="nav-link">法律讨论</RouterLink>
        <RouterLink to="/profile" class="nav-link">个人空间</RouterLink>
      </div>
    </nav>
    
    <!-- 主内容区域 -->
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-nav {
  background-color: #2c3e50;
  color: white;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-logo a {
  color: white;
  font-size: 1.5em;
  font-weight: bold;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 20px;
}

.nav-link {
  color: #ddd;
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-link.router-link-active {
  color: white;
  font-weight: bold;
  background-color: rgba(255, 255, 255, 0.2);
}

.main-content {
  flex: 1;
  background-color: #f5f5f5;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-nav {
    flex-direction: column;
    height: auto;
    padding: 10px;
  }
  
  .nav-logo {
    margin-bottom: 10px;
  }
  
  .nav-links {
    width: 100%;
    justify-content: space-between;
  }
  
  .nav-link {
    padding: 8px;
    font-size: 0.9em;
  }
}
</style>

<style>
/* 全局样式 */
body {
  margin: 0;
  padding: 0;
  font-family: Arial, sans-serif;
}

* {
  box-sizing: border-box;
}
</style>
