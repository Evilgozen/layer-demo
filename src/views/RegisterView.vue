<template>
  <div class="register-container">
    <a-card class="register-card" title="理工包青天 - 法律援助助手">
      <a-typography-title level="2" class="register-title">用户注册</a-typography-title>
      
      <a-alert v-if="userStore.error" type="error" :message="userStore.error" show-icon class="register-alert" />
      
      <a-form
        :model="formState"
        name="register-form"
        @finish="handleRegister"
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
          name="email"
          label="邮箱"
          :rules="[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' }
          ]"
        >
          <a-input 
            v-model:value="formState.email"
            placeholder="请输入邮箱"
            size="large"
          >
            <template #prefix>
              <mail-outlined />
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
          name="password"
          label="密码"
          :rules="[
            { required: true, message: '请输入密码' },
            { min: 6, message: '密码长度至少为6位' }
          ]"
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

        <a-form-item
          name="confirmPassword"
          label="确认密码"
          :rules="[
            { required: true, message: '请再次输入密码' },
            { validator: validateConfirmPassword }
          ]"
        >
          <a-input-password
            v-model:value="formState.confirmPassword"
            placeholder="请再次输入密码"
            size="large"
          >
            <template #prefix>
              <safety-outlined />
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
            class="register-button"
          >
            {{ userStore.loading ? '注册中...' : '注册' }}
          </a-button>
        </a-form-item>
      </a-form>
      
      <div class="register-links">
        <router-link to="/login" class="login-link">
          已有账号？立即登录
        </router-link>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { UserOutlined, LockOutlined, MailOutlined, SafetyOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const formState = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = async (rule, value) => {
  if (value === '') {
    return Promise.reject('请再次输入密码')
  }
  
  if (value !== formState.password) {
    return Promise.reject('两次输入的密码不一致')
  }
  
  return Promise.resolve()
}

const handleRegister = async () => {
  try {
    await userStore.register({
      username: formState.username,
      email: formState.email,
      password: formState.password
    })
    
    // Registration successful, redirect to login
    router.push('/login')
  } catch (error) {
    console.error('Registration error:', error)
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  min-height: 100vh;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.register-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="%23ffffff" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>') repeat;
  pointer-events: none;
}

.register-card {
  width: 100%;
  max-width: 480px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.2);
  animation: slideUp 0.6s ease-out;
  position: relative;
  z-index: 1;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.register-card :deep(.ant-card-head) {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  border-radius: 20px 20px 0 0;
  border-bottom: none;
}

.register-card :deep(.ant-card-head-title) {
  color: white;
  font-weight: 600;
  text-align: center;
  font-size: 18px;
}

.register-card :deep(.ant-card-body) {
  padding: 32px;
}

.register-title {
  text-align: center;
  margin-bottom: 32px;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
}

.register-button {
  margin-top: 16px;
  height: 48px;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
}

.register-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(118, 75, 162, 0.4);
}

.register-button:active {
  transform: translateY(0);
}

.login-links {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.login-link {
  color: #764ba2;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s ease;
  padding: 8px 16px;
  border-radius: 8px;
}

.login-link:hover {
  background: rgba(118, 75, 162, 0.1);
  color: #667eea;
  transform: translateY(-1px);
}

.register-alert {
  margin-bottom: 24px;
  border-radius: 12px;
}

:deep(.ant-input) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

:deep(.ant-input:focus) {
  border-color: #764ba2;
  box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.1);
}

:deep(.ant-input-affix-wrapper) {
  border-radius: 12px;
  border: 2px solid #e8e8e8;
  transition: all 0.3s ease;
}

:deep(.ant-input-affix-wrapper:focus-within) {
  border-color: #764ba2;
  box-shadow: 0 0 0 3px rgba(118, 75, 162, 0.1);
}

:deep(.ant-form-item-label > label) {
  font-weight: 600;
  color: #333;
}

:deep(.ant-form-item-has-error .ant-input) {
  border-color: #ff4d4f;
}

:deep(.ant-form-item-has-error .ant-input-affix-wrapper) {
  border-color: #ff4d4f;
}
</style>
