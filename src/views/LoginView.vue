<template>
  <div class="login-container">
    <a-card class="login-card" title="理工包青天 - 法律援助助手">
      <a-typography-title :level="2" class="login-title">用户登录</a-typography-title>
      
      <a-alert v-if="userStore.error" type="error" :message="userStore.error" show-icon class="login-alert" />
      
      <a-form
        :model="formState"
        name="login-form"
        @finish="handleLogin"
        autocomplete="off"
        layout="vertical"
      >
        <a-form-item
          name="username"
          label="用户名"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input 
            v-model:value="formState.username"
            placeholder="请输入用户名"
            size="large"
          >
            <template #prefix>
              <user-outlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          name="password"
          label="密码"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password
            v-model:value="formState.password"
            placeholder="请输入密码"
            size="large"
          >
            <template #prefix>
              <lock-outlined />
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="userStore.loading"
            block
            size="large"
            class="login-button"
          >
            {{ userStore.loading ? '登录中...' : '登录' }}
          </a-button>
        </a-form-item>
      </a-form>
      
      <div class="login-links">
        <router-link to="/register" class="register-link">
          没有账号？立即注册
        </router-link>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const formState = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  try {
    const result = await userStore.login(formState.username, formState.password)
    if (result && result.success) {
      // 登录成功后跳转到AI助手询问界面
      router.push('/')
    }
  } catch (error) {
    console.error('Login error:', error)
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background-color: #f5f5f5;
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); 
  border-radius: 8px;
}

.login-title {
  text-align: center;
  margin-bottom: 24px;
  color: #1890ff;
}

.login-button {
  margin-top: 12px;
  height: 44px;
}

.login-links {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.register-link {
  color: #1890ff;
  font-size: 14px;
}

.login-alert {
  margin-bottom: 24px;
}
</style>
