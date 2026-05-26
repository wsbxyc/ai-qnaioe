import http from './http.js'

export const techAssistantService = {
  async sendQuery(requestData) {
    try {
      const response = await http.post('/tech-assistant/query', requestData)
      return response.data
    } catch (error) {
      console.error('技术问答API调用失败:', error)

      if (error.response?.status === 404) {
        throw new Error('技术助手服务未启动，请检查后端服务')
      } else if (error.code === 'ECONNREFUSED') {
        throw new Error('无法连接到技术助手服务，请检查服务是否运行在8080端口')
      } else {
        throw new Error('技术问答服务暂时不可用，请稍后再试')
      }
    }
  },

  async detectIntent(query) {
    try {
      const response = await http.post('/tech-assistant/intent', { query })
      return response.data
    } catch (error) {
      console.error('意图识别API调用失败:', error)
      throw new Error('意图识别服务暂时不可用')
    }
  },

  async hybridRetrieve(requestData) {
    try {
      const response = await http.post('/tech-assistant/retrieve', requestData)
      return response.data
    } catch (error) {
      console.error('混合检索API调用失败:', error)
      throw new Error('检索服务暂时不可用')
    }
  },

  async healthCheck() {
    try {
      const response = await http.get('/tech-assistant/health')
      return response.status === 200
    } catch (error) {
      console.error('健康检查失败:', error)
      return false
    }
  }
}

export default http
