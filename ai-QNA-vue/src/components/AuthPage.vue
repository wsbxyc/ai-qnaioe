<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1 class="title">AI 技术助手</h1>
      <p class="subtitle">登录或注册以开始使用</p>
      
      <div class="tabs">
        <button 
          :class="{ active: isLoginMode }"
          @click="isLoginMode = true; clearError()"
        >
          登录
        </button>
        <button 
          :class="{ active: !isLoginMode }"
          @click="isLoginMode = false; clearError()"
        >
          注册
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="auth-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            placeholder="请输入用户名"
            required
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            required
            :minlength="isLoginMode ? 1 : 6"
          />
        </div>

        <div v-if="!isLoginMode" class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="formData.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            required
            minlength="6"
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button 
          type="submit" 
          class="submit-btn"
          :disabled="isLoading"
        >
          {{ isLoading ? '请稍候...' : (isLoginMode ? '登录' : '注册') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { authService } from '../services/api.js'

const emit = defineEmits(['login-success'])

const isLoginMode = ref(true)
const isLoading = ref(false)
const errorMessage = ref('')
const formData = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

const clearError = () => {
  errorMessage.value = ''
}

const handleSubmit = async () => {
  if (!formData.value.username || !formData.value.password) {
    errorMessage.value = '请填写所有必填项'
    return
  }

  if (!isLoginMode.value && formData.value.password !== formData.value.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  if (!isLoginMode.value && formData.value.password.length < 6) {
    errorMessage.value = '密码长度至少为6位'
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    let result
    if (isLoginMode.value) {
      result = await authService.login(formData.value.username, formData.value.password)
    } else {
      result = await authService.register(formData.value.username, formData.value.password)
    }

    if (result.success) {
      emit('login-success')
    } else {
      errorMessage.value = result.message || '操作失败'
    }
  } catch (error) {
    errorMessage.value = '网络错误，请稍后再试'
    console.error('Auth error:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.auth-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin: 0 0 8px 0;
  text-align: center;
}

.subtitle {
  color: #666;
  text-align: center;
  margin: 0 0 32px 0;
  font-size: 14px;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 32px;
  background: #f5f5f5;
  padding: 4px;
  border-radius: 8px;
}

.tabs button {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.tabs button:hover {
  color: #667eea;
}

.tabs button.active {
  background: white;
  color: #667eea;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.form-group input {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  text-align: center;
}

.submit-btn {
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
