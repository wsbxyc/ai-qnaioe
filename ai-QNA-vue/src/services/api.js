import http, { TOKEN_KEY, USER_KEY } from './http.js'

const api = http

export { TOKEN_KEY, USER_KEY }

/**
 * 后端 JPA 实体里 messages 为 String（存 JSON 文本），ChatSessionRequest 同字段为 String。
 * 请求体若传 JSON 数组会触发 HttpMessageNotReadableException。
 */
function serializeSessionMessages(messages) {
  const arr = Array.isArray(messages) ? messages : []
  return JSON.stringify(arr)
}

function parseSessionMessages(raw) {
  if (raw == null || raw === '') return []
  if (Array.isArray(raw)) return raw
  try {
    const p = JSON.parse(raw)
    return Array.isArray(p) ? p : []
  } catch {
    return []
  }
}

export const authService = {
  async register(username, password, email = '') {
    try {
      const response = await api.post('/auth/register', { username, password, email })
      const data = response.data
      if (data.success) {
        localStorage.setItem(TOKEN_KEY, data.token)
        localStorage.setItem(USER_KEY, JSON.stringify({ userId: data.userId, username: data.username }))
      }
      return data
    } catch (error) {
      console.error('注册失败:', error)
      return { success: false, message: '注册失败，请稍后再试' }
    }
  },

  async login(username, password) {
    try {
      const response = await api.post('/auth/login', { username, password })
      const data = response.data
      if (data.success) {
        localStorage.setItem(TOKEN_KEY, data.token)
        localStorage.setItem(USER_KEY, JSON.stringify({ userId: data.userId, username: data.username }))
      }
      return data
    } catch (error) {
      console.error('登录失败:', error)
      return { success: false, message: '登录失败，请稍后再试' }
    }
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },

  isAuthenticated() {
    return !!localStorage.getItem(TOKEN_KEY)
  },

  getUser() {
    const user = localStorage.getItem(USER_KEY)
    return user ? JSON.parse(user) : null
  }
}

export const sessionService = {
  async getSessions() {
    try {
      const response = await api.get('/sessions')
      const data = response.data
      if (data.success && Array.isArray(data.data)) {
        data.data = data.data.map((s) => ({
          ...s,
          messages: parseSessionMessages(s.messages)
        }))
      }
      return data
    } catch (error) {
      console.error('获取会话失败:', error)
      return { success: false, message: '获取会话失败' }
    }
  },

  async createSession(title) {
    try {
      const response = await api.post('/sessions', {
        title,
        messages: serializeSessionMessages([])
      })
      return response.data
    } catch (error) {
      console.error('创建会话失败:', error)
      return { success: false, message: '创建会话失败' }
    }
  },

  async updateSession(id, title, messages) {
    try {
      const response = await api.put(`/sessions/${id}`, {
        title,
        messages: serializeSessionMessages(messages)
      })
      return response.data
    } catch (error) {
      console.error('更新会话失败:', error)
      return { success: false, message: '更新会话失败' }
    }
  },

  async deleteSession(id) {
    try {
      const response = await api.delete(`/sessions/${id}`)
      return response.data
    } catch (error) {
      console.error('删除会话失败:', error)
      return { success: false, message: '删除会话失败' }
    }
  }
}

export const chatService = {
  async sendMessage(query, techStack = null, category = null, sessionId = null) {
    try {
      const requestData = { query }
      if (techStack) requestData.techStack = techStack
      if (category) requestData.category = category
      if (sessionId) requestData.sessionId = sessionId

      const response = await api.post('/tech-assistant/query', requestData)
      return response.data
    } catch (error) {
      console.error('API调用失败:', error)
      throw new Error('网络请求失败，请检查后端服务是否启动')
    }
  },

  async healthCheck() {
    try {
      const response = await api.get('/tech-assistant/health')
      return response.status === 200
    } catch (error) {
      console.error('健康检查失败:', error)
      return false
    }
  }
}

export default api
