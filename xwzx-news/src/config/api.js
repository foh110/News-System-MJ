/**
 * API配置文件
 * 包含API基础URL和AI问答功能所需的API参数
 */

// API基础URL配置
// 优先使用环境变量，否则使用默认值
export const apiConfig = {
  // 后端API基础URL
  // 开发环境: http://localhost:8000
  // 生产环境: 通过环境变量 VITE_API_BASE_URL 配置
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
}

export const aiChatConfig = {
  // OpenAI API地址
  apiEndpoint: 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  
  // API Key (由开发人员指定)
  apiKey: 'sk-eb4ce97ababe48aabf81092d12a39706',
  
  // 使用的模型 - 升级到支持联网搜索的版本
  model: 'qwen-plus'  // 或 qwen-max
}
