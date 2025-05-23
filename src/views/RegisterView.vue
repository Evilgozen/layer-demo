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
  min-height: 90vh;
  background-color: #f5f5f5;
  padding: 24px;
}

.register-card {
  width: 100%;
  max-width: 420px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border-radius: 8px;
}

.register-title {
  text-align: center;
  margin-bottom: 24px;
  color: #1890ff;
}

.register-button {
  margin-top: 12px;
  height: 44px;
}

.register-links {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.login-link {
  color: #1890ff;
  font-size: 14px;
}

.register-alert {
  margin-bottom: 24px;
}
</style>
