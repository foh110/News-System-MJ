<template>
  <div class="ai-chat-container">
    <van-nav-bar 
      title="AI问答" 
      fixed 
      :style="{ top: '30px' }"
      right-text="清空"
      @click-right="clearHistory"
    />
    
    <div class="chat-content">
      <div class="messages-container" ref="messagesContainer">
        <div 
          v-for="(message, index) in messages" 
          :key="index" 
          :class="['message', message.role === 'user' ? 'user-message' : 'ai-message']"
        >
          <div class="message-content">
            <div v-if="message.role === 'assistant' && message.content === ''" class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <div v-else v-html="formatMessage(message.content)"></div>
          </div>
        </div>
      </div>
      
      <div class="input-container">
        <van-field
          v-model="userInput"
          rows="1"
          autosize
          type="textarea"
          placeholder="请输入问题..."
          class="chat-input"
          @keypress.enter.prevent="sendMessage"
        />
        <van-button 
          type="primary" 
          class="send-button" 
          :disabled="isLoading || !userInput.trim()" 
          @click="sendMessage"
        >
          发送
        </van-button>
      </div>
    </div>
    
    <tab-bar />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';
import TabBar from '../components/TabBar.vue';
import { showToast, showDialog } from 'vant';
import * as marked from 'marked';
import DOMPurify from 'dompurify';
import { aiChatConfig, apiConfig } from '../config/api';

// 从 localStorage 加载历史记录
const loadHistory = () => {
  try {
    const saved = localStorage.getItem('ai_chat_history');
    if (saved) {
      messages.value = JSON.parse(saved);
    }
  } catch (e) {
    console.error('加载历史记录失败:', e);
  }
};

// 保存到 localStorage
const saveHistory = () => {
  try {
    // 只保存最近 50 条消息
    const toSave = messages.value.slice(-50);
    localStorage.setItem('ai_chat_history', JSON.stringify(toSave));
  } catch (e) {
    console.error('保存历史记录失败:', e);
  }
};

// 清空历史记录
const clearHistory = () => {
  showDialog({
    title: '提示',
    message: '确定要清空所有聊天记录吗？',
    showCancelButton: true,
  }).then(() => {
    messages.value = [
      { role: 'assistant', content: '你好！我是 AI 助手，有什么可以帮助你的吗？' }
    ];
    localStorage.removeItem('ai_chat_history');
    showToast('聊天记录已清空');
  }).catch(() => {});
};

// 聊天消息
const messages = ref([
  { role: 'assistant', content: '你好！我是 AI 助手，有什么可以帮助你的吗？' }
]);
const userInput = ref('');
const messagesContainer = ref(null);
const isLoading = ref(false);

// 从配置文件获取API设置
const apiEndpoint = ref(aiChatConfig.apiEndpoint);
const apiKey = ref(aiChatConfig.apiKey);
const model = ref(aiChatConfig.model);

// 调试：打印配置值
console.log('API Config loaded:', {
  endpoint: apiEndpoint.value,
  keyPrefix: apiKey.value ? apiKey.value.substring(0, 5) + '...' : 'EMPTY',
  model: model.value
});

// 格式化消息内容（支持Markdown）
const formatMessage = (content) => {
  if (!content) return '';
  // 使用marked解析Markdown，并用DOMPurify清理HTML
  return DOMPurify.sanitize(marked.parse(content));
};

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;
  
  // 检查 API 设置
  if (!apiKey.value || apiKey.value === 'your-api-key-here') {
    showToast('API Key 未配置，请联系管理员');
    return;
  }
  
  // 添加用户消息
  const userMessage = userInput.value.trim();
  messages.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  
  // 添加 AI 消息占位
  messages.value.push({ role: 'assistant', content: '' });
  
  // 保存历史记录
  saveHistory();
  
  // 滚动到底部
  await nextTick();
  scrollToBottom();
  
  // 发送请求（传入上下文信息）
  isLoading.value = true;
  try {
    await fetchAIResponse(userMessage);
    // 保存 AI 回复
    saveHistory();
  } catch (error) {
    console.error('Error fetching AI response:', error);
    // 更新最后一条消息为错误信息
    messages.value[messages.value.length - 1].content = `发生错误: ${error.message || '请检查网络连接和 API 设置'}`;
    saveHistory();
  } finally {
    isLoading.value = false;
    await nextTick();
    scrollToBottom();
  }
};

// 获取上下文信息（当前时间 + 实时新闻）
const getContextInfo = async () => {
  const now = new Date();
  const timeInfo = `当前时间：${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 ${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
  
  let newsInfo = '';
  
  // 优先尝试获取实时新闻
  try {
    const response = await fetch(`${apiConfig.baseURL}/api/search/news`);
    const data = await response.json();
    
    if (data.code === 200 && data.data.news && data.data.news.length > 0) {
      const newsTitles = data.data.news.map(n => `- ${n.title}`).join('\n');
      newsInfo = `\n\n最新实时新闻：\n${newsTitles}`;
      return `${timeInfo}${newsInfo}`;
    }
  } catch (e) {
    console.log('实时新闻获取失败，使用本地新闻');
  }
  
  // 降级方案：使用本地数据库新闻
  try {
    const localResponse = await fetch(`${apiConfig.baseURL}/api/news/list?categoryId=1&page=1&pageSize=5`);
    const localData = await localResponse.json();
    if (localData.code === 200 && localData.data.list) {
      const newsTitles = localData.data.list.map(n => `- ${n.title}`).join('\n');
      newsInfo = `\n\n本地新闻库：\n${newsTitles}`;
    }
  } catch (e) {
    console.error('获取新闻失败:', e);
  }
  
  return `${timeInfo}${newsInfo}`;
};

// 获取AI响应（使用SSE）
const fetchAIResponse = async (userMessage) => {
  // 获取实时上下文
  const contextInfo = await getContextInfo();
  
  const allMessages = messages.value
    .slice(0, -1) // 排除最后一个空的assistant消息
    .map(msg => ({ role: msg.role, content: msg.content }));
  
  // 在系统消息中注入上下文
  const systemMessage = {
    role: 'system',
    content: `你是一个智能新闻助手。以下是实时信息，请据此回答问题：\n${contextInfo}\n\n回答规则：\n1. 如果用户问时间，请直接回答当前时间。\n2. 如果用户问新闻或时事，请引用上述实时新闻。\n3. 如果新闻中没有相关信息，请说明暂时没有找到相关内容。\n4. 保持回答简洁专业。`
  };
  
  try {
    const cleanApiKey = apiKey.value ? apiKey.value.trim() : '';
    console.log('=== DEBUG ===');
    console.log('apiKey.value:', apiKey.value);
    console.log('cleanApiKey:', cleanApiKey);
    console.log('cleanApiKey length:', cleanApiKey.length);
    console.log('Authorization header:', `Bearer ${cleanApiKey}`);
    
    if (!cleanApiKey) {
      throw new Error('API Key is empty after trim');
    }
    
    const response = await fetch(apiEndpoint.value, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${cleanApiKey}`,
        'X-DashScope-SSE': 'enable'
      },
      body: JSON.stringify({
        model: model.value,
        messages: [systemMessage, ...allMessages],
        stream: true,
        enable_search: true  // 开启通义千问联网搜索
      })
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.error?.message || `HTTP error! status: ${response.status}`);
    }
    
    // 处理 SSE 流
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let aiResponse = '';
    
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
      
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
      
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') continue;
          
        try {
          const json = JSON.parse(data);
          // 适配阿里云 DashScope 的返回格式
          const content = json.choices?.[0]?.delta?.content || 
                         json.output?.text || 
                         json.choices?.[0]?.message?.content || '';
          if (content) {
            aiResponse += content;
            // 立即更新最后一条消息（流式显示）
            messages.value[messages.value.length - 1].content = aiResponse;
            // 强制滚动到底部
            await nextTick();
            scrollToBottom();
          }
        } catch (e) {
          console.error('Error parsing SSE data:', e);
        }
      }
    }
  }
  
  // 如果没有收到任何内容
  if (!aiResponse) {
    messages.value[messages.value.length - 1].content = '抱歉，我无法生成回复。请检查API设置或稍后再试。';
  }
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
};

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

// 监听消息变化，自动滚动
watch(messages, () => {
  nextTick(scrollToBottom);
}, { deep: true });

// 组件挂载时加载历史记录
onMounted(() => {
  loadHistory();
  scrollToBottom();
});
</script>

<style scoped>
.ai-chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding-top: 76px;
  padding-bottom: 50px;
  box-sizing: border-box;
}

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.message {
  margin-bottom: 10px;
  max-width: 80%;
}

.user-message {
  margin-left: auto;
}

.ai-message {
  margin-right: auto;
}

.message-content {
  padding: 10px;
  border-radius: 10px;
  word-break: break-word;
}

.user-message .message-content {
  background-color: #007aff;
  color: white;
}

.ai-message .message-content {
  background-color: #f2f2f2;
  color: #333;
}

.input-container {
  display: flex;
  padding: 10px;
  border-top: 1px solid #eee;
  background-color: #fff;
}

.chat-input {
  flex: 1;
  margin-right: 10px;
}

.send-button {
  align-self: flex-end;
}

/* Markdown 样式 */
.message-content pre {
  background-color: #f8f8f8;
  padding: 10px;
  border-radius: 5px;
  overflow-x: auto;
}

.message-content code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 4px;
  border-radius: 3px;
}

.message-content img {
  max-width: 100%;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  padding: 5px;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  background-color: #999;
  border-radius: 50%;
  margin: 0 2px;
  display: inline-block;
  animation: bounce 1.5s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-5px);
  }
}

/* Markdown样式 */
:deep(pre) {
  background-color: #f0f0f0;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
}

:deep(code) {
  font-family: monospace;
  background-color: #f0f0f0;
  padding: 2px 4px;
  border-radius: 4px;
}

:deep(p) {
  margin: 8px 0;
}

:deep(ul), :deep(ol) {
  padding-left: 20px;
}

:deep(a) {
  color: #1989fa;
  text-decoration: none;
}
</style>