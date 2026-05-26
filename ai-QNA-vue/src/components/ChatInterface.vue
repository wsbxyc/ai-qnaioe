<template>
  <div class="chat-container">
    <div class="chat-header">
      <h1>医药知识智能问答系统</h1>
      <div class="status-indicator" :class="{ online: isBackendOnline, offline: !isBackendOnline }">
        {{ isBackendOnline ? '后端服务在线' : '后端服务离线' }}
      </div>
    </div>
    
    <div class="chat-messages" ref="messagesContainer">
      <div 
        v-for="(message, index) in messages" 
        :key="index" 
        :class="['message', message.type]"
      >
        <div class="message-content">
          <div class="message-text">{{ message.text }}</div>
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>
        </div>
      </div>
      
      <div v-if="isLoading" class="message ai loading">
        <div class="message-content">
          <div class="message-text">AI正在思考中...</div>
        </div>
      </div>
    </div>
    
    <div class="chat-input-container">
      <div class="input-group">
        <input
          v-model="inputMessage"
          type="text"
          placeholder="请输入您的医药相关问题..."
          @keyup.enter="sendMessage"
          :disabled="isLoading || !isBackendOnline"
          class="message-input"
        />
        <button 
          @click="sendMessage" 
          :disabled="!inputMessage.trim() || isLoading || !isBackendOnline"
          class="send-button"
        >
          发送
        </button>
      </div>
      <div class="input-hint">
        例如：阿司匹林的副作用有哪些？感冒药应该怎么选择？
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { chatService } from '../services/api.js'

const messages = ref([])
const inputMessage = ref('')
const isLoading = ref(false)
const isBackendOnline = ref(false)
const messagesContainer = ref(null)

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const checkBackendStatus = async () => {
  try {
    isBackendOnline.value = await chatService.healthCheck()
  } catch (error) {
    isBackendOnline.value = false
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value || !isBackendOnline.value) {
    return
  }

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  messages.value.push({
    type: 'user',
    text: userMessage,
    timestamp: Date.now()
  })

  isLoading.value = true
  scrollToBottom()

  try {
    const response = await chatService.sendMessage(userMessage)
    
    messages.value.push({
      type: 'ai',
      text: response.answer,
      timestamp: response.timestamp
    })
  } catch (error) {
    messages.value.push({
      type: 'ai error',
      text: error.message || '抱歉，AI服务暂时不可用，请稍后再试。',
      timestamp: Date.now()
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  checkBackendStatus()
  
  setInterval(checkBackendStatus, 30000)
  
  messages.value.push({
    type: 'ai',
    text: '您好！我是医药知识智能助手，可以为您解答医药相关问题。请告诉我您想了解什么？',
    timestamp: Date.now()
  })
})

watch(messages, scrollToBottom, { deep: true })
</script>

<style scoped>
.chat-container {
  max-width: 800px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.chat-header {
  background: #2c3e50;
  color: white;
  padding: 1rem;
  text-align: center;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.status-indicator {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: bold;
}

.status-indicator.online {
  background: #27ae60;
  color: white;
}

.status-indicator.offline {
  background: #e74c3c;
  color: white;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  display: flex;
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
}

.message.ai {
  align-self: flex-start;
}

.message.error {
  align-self: center;
  max-width: 90%;
}

.message-content {
  padding: 0.75rem 1rem;
  border-radius: 18px;
  position: relative;
}

.message.user .message-content {
  background: #3498db;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.ai .message-content {
  background: white;
  color: #333;
  border: 1px solid #ddd;
  border-bottom-left-radius: 4px;
}

.message.error .message-content {
  background: #ffeaa7;
  color: #d63031;
  border-radius: 8px;
  text-align: center;
}

.message.loading .message-content {
  background: #f8f9fa;
  color: #6c757d;
  font-style: italic;
}

.message-time {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 0.25rem;
}

.chat-input-container {
  padding: 1rem;
  background: white;
  border-top: 1px solid #ddd;
}

.input-group {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.message-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 1rem;
}

.message-input:focus {
  outline: none;
  border-color: #3498db;
}

.message-input:disabled {
  background: #f8f9fa;
  cursor: not-allowed;
}

.send-button {
  padding: 0.75rem 1.5rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
}

.send-button:hover:not(:disabled) {
  background: #2980b9;
}

.send-button:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.input-hint {
  font-size: 0.875rem;
  color: #7f8c8d;
  text-align: center;
}
</style>