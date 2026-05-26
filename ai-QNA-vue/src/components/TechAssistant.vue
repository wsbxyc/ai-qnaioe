<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-top">
        <button class="new-chat-btn" @click="createNewChat">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          <span v-if="!sidebarCollapsed">新建对话</span>
        </button>
      </div>

      <div class="sidebar-chats" v-if="!sidebarCollapsed">
        <div 
          v-for="chat in chats"
          :key="chat.id"
          class="chat-item"
          :class="{ active: chat.id === currentChatId }"
          @click="switchChat(chat.id)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="chat-title">{{ chat.title }}</span>
          <button class="chat-delete" @click.stop="deleteChat(chat.id)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>

      <div class="sidebar-bottom" v-if="!sidebarCollapsed">
        <div class="user-info">
          <div class="user-avatar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div class="user-details">
            <div class="user-name">{{ user?.username || '用户' }}</div>
          </div>
        </div>
        <button class="logout-btn" @click="handleLogout">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          退出登录
        </button>
      </div>
    </aside>

    <main class="main-area">
      <header class="main-header">
        <button class="toggle-sidebar" @click="sidebarCollapsed = !sidebarCollapsed">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
        </button>
        <div class="header-title">
          <span class="model-name">TechAssist</span>
          <span class="model-badge">v1.0</span>
        </div>
        <div class="header-status">
          <span class="status-dot" :class="isBackendOnline ? 'online' : 'offline'"></span>
          <span class="status-text">{{ isBackendOnline ? '在线' : '离线' }}</span>
        </div>
      </header>

      <div class="chat-body" ref="messagesContainer">
        <div v-if="currentMessages.length === 0" class="welcome-screen">
          <div class="welcome-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="1.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <h1 class="welcome-title">智能技术助手</h1>
          <p class="welcome-subtitle">配置 + API 双引擎，支持 Spring Boot、Docker、Java 等主流技术栈</p>
          
          <div class="quick-actions">
            <div class="quick-group">
              <div class="quick-label">配置查询</div>
              <button class="quick-btn" @click="fillExample('Spring Boot如何配置多数据源？')">Spring Boot 多数据源配置</button>
              <button class="quick-btn" @click="fillExample('Docker容器网络配置最佳实践')">Docker 网络配置</button>
              <button class="quick-btn" @click="fillExample('Redis缓存配置参数有哪些？')">Redis 缓存配置</button>
            </div>
            <div class="quick-group">
              <div class="quick-label">API 推荐</div>
              <button class="quick-btn" @click="fillExample('Java Stream API的使用示例')">Java Stream API</button>
              <button class="quick-btn" @click="fillExample('Vue 3 Composition API教程')">Vue 3 Composition API</button>
              <button class="quick-btn" @click="fillExample('Python装饰器的使用场景')">Python 装饰器</button>
            </div>
            <div class="quick-group">
              <div class="quick-label">故障排除</div>
              <button class="quick-btn" @click="fillExample('Spring Boot启动报错如何排查？')">Spring Boot 启动报错</button>
              <button class="quick-btn" @click="fillExample('MySQL索引优化建议')">MySQL 索引优化</button>
              <button class="quick-btn" @click="fillExample('微服务架构设计最佳实践')">微服务架构设计</button>
            </div>
          </div>
        </div>

        <div v-else class="messages-list">
          <div
            v-for="(message, index) in currentMessages"
            :key="index"
            :class="['message-row', message.type]"
          >
            <div class="message-avatar">
              <div v-if="message.type === 'user'" class="avatar user-avatar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </div>
              <div v-else class="avatar ai-avatar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
              </div>
            </div>
            <div class="message-body">
              <div class="message-sender">{{ message.type === 'user' ? '你' : 'TechAssist' }}</div>
              <div class="message-content" v-html="formatMessageText(message.text)"></div>
              <div v-if="message.relevantDocs && message.relevantDocs.length > 0" class="relevant-docs">
                <div class="docs-header">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  <span>相关文档 ({{ message.relevantDocs.length }})</span>
                </div>
                <div v-for="(doc, di) in message.relevantDocs" :key="di" class="doc-card">
                  <div class="doc-card-title">{{ doc.title }}</div>
                  <div class="doc-card-meta">
                    <span class="doc-tag">{{ doc.techStack }}</span>
                    <span class="doc-tag">{{ doc.category }}</span>
                    <span class="doc-score" :title="'融合/检索得分'">{{ Number(doc.score).toFixed(4) }}</span>
                  </div>
                </div>
              </div>
              <div v-if="message.intent" class="message-intent">
                <span class="intent-tag" :class="getIntentClass(message.intent)">{{ getIntentLabel(message.intent) }}</span>
              </div>
            </div>
          </div>

          <div v-if="isLoading" class="message-row ai">
            <div class="message-avatar">
              <div class="avatar ai-avatar thinking">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
              </div>
            </div>
            <div class="message-body">
              <div class="message-sender">TechAssist</div>
              <div class="message-content">
                <div class="thinking-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-wrapper">
          <div class="tech-stack-bar">
            <label>技术栈筛选</label>
            <select v-model="selectedTechStack" class="tech-stack-select">
              <option value="">全部</option>
              <option value="Spring Boot">Spring Boot</option>
              <option value="Docker">Docker</option>
              <option value="Java">Java</option>
              <option value="Python">Python</option>
              <option value="Vue">Vue</option>
              <option value="React">React</option>
              <option value="MySQL">MySQL</option>
              <option value="Redis">Redis</option>
              <option value="TypeScript">TypeScript</option>
              <option value="Node.js">Node.js</option>
              <option value="Kubernetes">Kubernetes</option>
              <option value="PostgreSQL">PostgreSQL</option>
              <option value="MongoDB">MongoDB</option>
            </select>
          </div>
          <div class="input-box">
            <textarea
              ref="inputRef"
              v-model="inputMessage"
              placeholder="输入技术问题..."
              @keydown.enter.exact="sendMessage"
              @input="autoResize"
              rows="1"
              :disabled="isLoading || !isBackendOnline"
            ></textarea>
            <button
              class="send-btn"
              @click="sendMessage"
              :disabled="!inputMessage.trim() || isLoading || !isBackendOnline"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
          <div class="input-footer">
            <span>TechAssist 可能会产生不准确的信息，请注意甄别</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { techAssistantService } from '../services/tech-api.js'
import { authService, sessionService } from '../services/api.js'

const emit = defineEmits(['logout'])

const user = ref(authService.getUser())
const chats = ref([])
const currentChatId = ref(null)
const currentSessionId = ref(null)
const inputMessage = ref('')
const isLoading = ref(false)
const isBackendOnline = ref(false)
const messagesContainer = ref(null)
const inputRef = ref(null)
const sidebarCollapsed = ref(false)
const selectedTechStack = ref('')

const currentMessages = computed(() => {
  const chat = chats.value.find(c => c.id === currentChatId.value)
  return chat ? chat.messages : []
})

const loadSessions = async () => {
  try {
    const result = await sessionService.getSessions()
    if (result.success && result.data) {
      chats.value = result.data.map(session => ({
        id: session.id,
        title: session.title,
        messages: session.messages || [],
        createdAt: session.createdAt
      }))
    }
  } catch (error) {
    console.error('加载会话失败:', error)
  }
}

const saveCurrentSession = async () => {
  if (!currentSessionId.value || !currentChatId.value) return
  
  const chat = chats.value.find(c => c.id === currentChatId.value)
  if (!chat) return

  try {
    await sessionService.updateSession(currentSessionId.value, chat.title, chat.messages)
  } catch (error) {
    console.error('保存会话失败:', error)
  }
}

const createNewChat = async () => {
  if (currentSessionId.value) {
    await saveCurrentSession()
  }

  const result = await sessionService.createSession('新对话')
  if (result.success && result.data) {
    const chat = {
      id: result.data.id,
      title: '新对话',
      messages: [],
      createdAt: result.data.createdAt
    }
    chats.value.unshift(chat)
    currentChatId.value = chat.id
    currentSessionId.value = result.data.id
  }
}

const switchChat = (id) => {
  if (currentSessionId.value) {
    saveCurrentSession()
  }
  currentChatId.value = id
  currentSessionId.value = id
}

const deleteChat = async (id) => {
  try {
    await sessionService.deleteSession(id)
    chats.value = chats.value.filter(c => c.id !== id)
    if (currentChatId.value === id) {
      if (chats.value.length > 0) {
        currentChatId.value = chats.value[0].id
        currentSessionId.value = chats.value[0].id
      } else {
        currentChatId.value = null
        currentSessionId.value = null
      }
    }
  } catch (error) {
    console.error('删除会话失败:', error)
  }
}

const handleLogout = () => {
  authService.logout()
  emit('logout')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const autoResize = () => {
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
      inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 200) + 'px'
    }
  })
}

const checkBackendStatus = async () => {
  try {
    isBackendOnline.value = await techAssistantService.healthCheck()
  } catch {
    isBackendOnline.value = false
  }
}

const getIntentLabel = (intent) => {
  const map = {
    'CONFIG_QUERY': '配置查询',
    'API_RECOMMENDATION': 'API推荐',
    'TROUBLESHOOTING': '故障排除',
    'GENERAL_KNOWLEDGE': '通用知识'
  }
  return map[intent] || intent
}

const getIntentClass = (intent) => {
  return intent.toLowerCase().replace('_', '-')
}

const formatMessageText = (text) => {
  return text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/\n/g, '<br>')
}

const fillExample = (example) => {
  if (!currentChatId.value) createNewChat()
  inputMessage.value = example
  nextTick(() => {
    if (inputRef.value) inputRef.value.focus()
  })
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value || !isBackendOnline.value) return

  if (!currentChatId.value) {
    await createNewChat()
  }

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.style.height = 'auto'
    }
  })

  const chat = chats.value.find(c => c.id === currentChatId.value)
  if (!chat) return

  chat.messages.push({
    type: 'user',
    text: userMessage
  })

  if (chat.messages.length === 1) {
    chat.title = userMessage.length > 20 ? userMessage.substring(0, 20) + '...' : userMessage
  }

  isLoading.value = true
  scrollToBottom()

  try {
    const response = await techAssistantService.sendQuery({
      query: userMessage,
      techStack: selectedTechStack.value || '',
      category: ''
    })

    chat.messages.push({
      type: 'ai',
      text: response.answer,
      intent: response.intent,
      confidence: response.confidence,
      relevantDocs: response.relevantDocuments
    })

    await saveCurrentSession()
  } catch (error) {
    chat.messages.push({
      type: 'ai',
      text: error.message || '抱歉，技术助手服务暂时不可用，请稍后再试。'
    })
    await saveCurrentSession()
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

onMounted(() => {
  loadSessions()
  checkBackendStatus()
  setInterval(checkBackendStatus, 30000)
})

watch(currentMessages, scrollToBottom, { deep: true })
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 260px;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  transition: width 0.2s ease;
  flex-shrink: 0;
}
.sidebar.collapsed {
  width: 0;
  border-right: none;
  overflow: hidden;
}

.sidebar-top {
  padding: 12px;
  border-bottom: 1px solid var(--border);
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--sidebar-text);
  cursor: pointer;
  font-size: 14px;
  transition: background 0.15s;
}
.new-chat-btn:hover {
  background: var(--sidebar-hover);
  color: var(--sidebar-text-hover);
}

.sidebar-chats {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.chat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--sidebar-text);
  font-size: 13px;
  transition: background 0.15s;
  position: relative;
}
.chat-item:hover {
  background: var(--sidebar-hover);
  color: var(--sidebar-text-hover);
}
.chat-item.active {
  background: var(--sidebar-active);
  color: var(--sidebar-text-hover);
}

.chat-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-delete {
  opacity: 0;
  background: none;
  border: none;
  color: var(--sidebar-text);
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: opacity 0.15s, color 0.15s;
}
.chat-item:hover .chat-delete {
  opacity: 1;
}
.chat-delete:hover {
  color: var(--danger);
}

.sidebar-bottom {
  padding: 12px;
  border-top: 1px solid var(--border);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: #5b5fc7;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--sidebar-text);
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--sidebar-text);
  cursor: pointer;
  font-size: 13px;
  transition: background 0.15s, color 0.15s;
}
.logout-btn:hover {
  background: var(--danger);
  color: white;
  border-color: var(--danger);
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--main-bg);
  flex-shrink: 0;
}

.toggle-sidebar {
  background: none;
  border: none;
  color: var(--msg-text-secondary);
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  transition: color 0.15s, background 0.15s;
}
.toggle-sidebar:hover {
  color: var(--msg-text);
  background: var(--sidebar-hover);
}

.header-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}
.model-name {
  font-weight: 600;
  font-size: 15px;
}
.model-badge {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--accent-light);
  color: var(--accent);
  border-radius: 4px;
  font-weight: 600;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 6px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.status-dot.online {
  background: var(--accent);
  box-shadow: 0 0 6px var(--accent);
}
.status-dot.offline {
  background: var(--danger);
}
.status-text {
  font-size: 12px;
  color: var(--msg-text-secondary);
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px 20px;
  text-align: center;
}

.welcome-icon {
  margin-bottom: 20px;
  opacity: 0.8;
}

.welcome-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--msg-text);
  margin-bottom: 8px;
}

.welcome-subtitle {
  font-size: 15px;
  color: var(--msg-text-secondary);
  margin-bottom: 40px;
  max-width: 500px;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  max-width: 720px;
  width: 100%;
}

.quick-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--msg-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.quick-btn {
  background: var(--msg-user-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  color: var(--msg-text);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s, border-color 0.15s;
  line-height: 1.4;
}
.quick-btn:hover {
  background: var(--sidebar-hover);
  border-color: var(--input-focus);
}

.messages-list {
  padding: 20px 0;
  max-width: 768px;
  margin: 0 auto;
  width: 100%;
}

.message-row {
  display: flex;
  gap: 16px;
  padding: 16px 24px;
  animation: msgIn 0.3s ease;
}
.message-row.user {
  background: var(--msg-user-bg);
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar {
  flex-shrink: 0;
  padding-top: 2px;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-avatar {
  background: #5b5fc7;
  color: white;
}
.ai-avatar {
  background: var(--accent);
  color: white;
}
.ai-avatar.thinking {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.message-body {
  flex: 1;
  min-width: 0;
}

.message-sender {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--msg-text);
}

.message-content {
  font-size: 15px;
  line-height: 1.7;
  color: var(--msg-text);
  word-break: break-word;
}
.message-content :deep(pre) {
  margin: 10px 0;
  border-radius: 8px;
  overflow-x: auto;
}
.message-content :deep(code) {
  font-size: 13px;
}

.relevant-docs {
  margin-top: 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.docs-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--tag-bg);
  font-size: 12px;
  font-weight: 600;
  color: var(--msg-text-secondary);
}

.doc-card {
  padding: 10px 12px;
  border-top: 1px solid var(--border);
}
.doc-card:first-of-type {
  border-top: none;
}

.doc-card-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--msg-text);
  margin-bottom: 4px;
}

.doc-card-meta {
  display: flex;
  gap: 6px;
  align-items: center;
}

.doc-tag {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--tag-bg);
  border-radius: 4px;
  color: var(--tag-text);
}

.doc-score {
  font-size: 11px;
  color: var(--accent);
  font-weight: 600;
}

.message-intent {
  margin-top: 8px;
}

.intent-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}
.intent-tag.config-query { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.intent-tag.api-recommendation { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
.intent-tag.troubleshooting { background: rgba(239, 68, 68, 0.15); color: #f87171; }
.intent-tag.general-knowledge { background: rgba(34, 197, 94, 0.15); color: #4ade80; }

.thinking-dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}
.thinking-dots span {
  width: 6px;
  height: 6px;
  background: var(--msg-text-secondary);
  border-radius: 50%;
  animation: dotBounce 1.4s ease-in-out infinite;
}
.thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
.thinking-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.input-area {
  padding: 12px 24px 20px;
  background: var(--main-bg);
  flex-shrink: 0;
}

.input-wrapper {
  max-width: 768px;
  margin: 0 auto;
}

.tech-stack-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.tech-stack-bar label {
  font-size: 12px;
  font-weight: 600;
  color: var(--msg-text-secondary);
  white-space: nowrap;
}
.tech-stack-select {
  flex: 1;
  max-width: 280px;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 8px;
  color: var(--msg-text);
  padding: 8px 10px;
  font-size: 13px;
  cursor: pointer;
}
.tech-stack-select:focus {
  outline: none;
  border-color: var(--input-focus);
}

.input-box {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 16px;
  padding: 10px 14px;
  transition: border-color 0.2s;
}
.input-box:focus-within {
  border-color: var(--input-focus);
}

.input-box textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--msg-text);
  font-size: 15px;
  line-height: 1.5;
  resize: none;
  max-height: 200px;
  padding: 2px 0;
}
.input-box textarea::placeholder {
  color: var(--msg-text-secondary);
}
.input-box textarea:disabled {
  opacity: 0.5;
}

.send-btn {
  background: var(--accent);
  border: none;
  border-radius: 8px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: white;
  flex-shrink: 0;
  transition: background 0.15s, opacity 0.15s;
}
.send-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}
.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.input-footer {
  text-align: center;
  padding-top: 8px;
  font-size: 11px;
  color: var(--msg-text-secondary);
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    z-index: 100;
    height: 100%;
  }
  .sidebar.collapsed {
    transform: translateX(-100%);
  }
  .quick-actions {
    grid-template-columns: 1fr;
  }
  .messages-list {
    padding: 12px 0;
  }
  .message-row {
    padding: 12px 16px;
  }
  .input-area {
    padding: 8px 12px 16px;
  }
}
</style>
