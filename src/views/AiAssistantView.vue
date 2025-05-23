<template>
  <div class="ai-assistant-container" :class="{ 'senior-mode': seniorMode }">
    <div class="header">
      <h1>法律咨询助手</h1>
      <div class="mode-controls">
        <label class="senior-mode-toggle">
          <input type="checkbox" v-model="seniorMode">
          <span class="toggle-label">老年模式</span>
        </label>
      </div>
      <div class="user-info" v-if="userStore.user">
        <span>欢迎, {{ userStore.user.username }}</span>
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </div>

    <div class="chat-container">
      <div class="chat-messages" ref="messagesContainer">
        <div 
          v-for="(message, index) in messages" 
          :key="index" 
          :class="['message', message.role === 'user' ? 'user-message' : 'assistant-message']"
        >
          <div class="message-content" v-if="message.role === 'user'">{{ message.content }}</div>
          <div class="message-content markdown-content" v-else v-html="renderMarkdown(message.content)"></div>
        </div>
        <div v-if="loading" class="loading-indicator">
          <span>AI思考中...</span>
        </div>
      </div>

      <div class="chat-input">
        <textarea 
          v-model="userInput" 
          placeholder="请输入您的法律问题..." 
          @keyup.enter.ctrl="sendMessage"
        ></textarea>
        <button @click="sendMessage" :disabled="loading || !userInput.trim()">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';
import { marked } from 'marked';
import { useUserStore } from '../stores/userStore';
import { useRouter } from 'vue-router';
import axios from 'axios';

const userStore = useUserStore();
const router = useRouter();
const userInput = ref('');
const seniorMode = ref(false);
const messages = ref([
  { role: 'assistant', content: '您好！我是您的法律咨询助手。请问有什么法律问题我可以帮您解答？' }
]);
const loading = ref(false);
const messagesContainer = ref(null);

// 检查用户是否已登录
onMounted(async () => {
  if (!userStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  
  if (!userStore.user) {
    await userStore.fetchUserData();
  }
});

// 自动滚动到最新消息
watch(messages, () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
});

// 发送消息到AI服务
async function sendMessage() {
  if (!userInput.value.trim() || loading.value) return;
  
  // 添加用户消息
  const userMessage = userInput.value.trim();
  messages.value.push({ role: 'user', content: userMessage });
  userInput.value = '';
  
  // 设置加载状态
  loading.value = true;
  
  try {
    // 准备发送到后端的消息格式
    const chatMessages = messages.value.map(msg => ({
      role: msg.role,
      content: msg.content
    }));
    
    // 调用后端AI聊天API
    const response = await axios.post('http://localhost:8000/ai/chat', {
      messages: chatMessages
    }, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      }
    });
    
    // 添加AI回复
    messages.value.push({ 
      role: 'assistant', 
      content: response.data.response 
    });
  } catch (error) {
    console.error('AI聊天请求失败:', error);
    messages.value.push({ 
      role: 'assistant', 
      content: '抱歉，我遇到了一些问题。请稍后再试或联系管理员。' 
    });
  } finally {
    loading.value = false;
  }
}

// 退出登录
function logout() {
  userStore.logout();
  router.push('/login');
}

// 渲染Markdown内容
function renderMarkdown(content) {
  if (!content) return '';
  try {
    // 配置marked选项
    marked.setOptions({
      breaks: true,      // 将\n转换为<br>
      gfm: true,         // 使用GitHub风格的Markdown
      headerIds: false,  // 不为标题生成ID
      mangle: false,     // 不转义内容
      sanitize: false    // 不净化HTML（注意：这可能有XSS风险，但对于AI生成的内容通常是安全的）
    });
    return marked(content);
  } catch (error) {
    console.error('Markdown渲染错误:', error);
    return content; // 如果渲染失败，返回原始内容
  }
}
</script>

<style scoped>
.ai-assistant-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  box-sizing: border-box;
  transition: all 0.3s ease;
}

/* 老年模式样式 */
.senior-mode {
  font-size: 120%;
  font-weight: 500;
}

.senior-mode button {
  font-size: 120%;
  font-weight: bold;
  padding: 12px 24px;
}

.senior-mode textarea {
  font-size: 120%;
  font-weight: 500;
  padding: 16px;
}

.senior-mode .message-content {
  font-size: 120%;
  font-weight: 500;
  line-height: 1.6;
}

.senior-mode h1 {
  font-size: 180%;
}

.senior-mode .user-info span {
  font-size: 120%;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e0e0e0;
  flex-wrap: wrap;
  gap: 10px;
}

.mode-controls {
  display: flex;
  align-items: center;
}

.senior-mode-toggle {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.senior-mode-toggle input {
  margin-right: 8px;
  width: 18px;
  height: 18px;
}

.toggle-label {
  color: #1976d2;
  font-weight: 500;
}

.header h1 {
  margin: 0;
  color: #333;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.logout-btn {
  background-color: transparent;
  border: 1px solid #d32f2f;
  color: #d32f2f;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  background-color: #d32f2f;
  color: white;
}

.chat-container {
  display: flex;
  flex-direction: column;
  flex-grow: 1;
  background-color: #f9f9f9;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.chat-messages {
  flex-grow: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-height: calc(100vh - 200px);
}

.message {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.5;
}

.user-message {
  align-self: flex-end;
  background-color: #1976d2;
  color: white;
}

.assistant-message {
  align-self: flex-start;
  background-color: white;
  border: 1px solid #e0e0e0;
  color: #333;
}

.message-content {
  white-space: pre-wrap;
}

.markdown-content {
  white-space: normal;
}

.markdown-content p {
  margin: 0.5em 0;
}

.markdown-content ul, .markdown-content ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.markdown-content h1, .markdown-content h2, .markdown-content h3,
.markdown-content h4, .markdown-content h5, .markdown-content h6 {
  margin: 0.5em 0;
  font-weight: bold;
}

.markdown-content code {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
}

.markdown-content pre {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 1em;
  border-radius: 5px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.markdown-content pre code {
  background-color: transparent;
  padding: 0;
}

.markdown-content blockquote {
  border-left: 4px solid #ddd;
  padding-left: 1em;
  margin: 0.5em 0;
  color: #666;
}

.markdown-content a {
  color: #1976d2;
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.5em 0;
}

.markdown-content th, .markdown-content td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.markdown-content th {
  background-color: #f2f2f2;
}

.loading-indicator {
  align-self: center;
  color: #666;
  margin: 10px 0;
  font-style: italic;
}

.chat-input {
  display: flex;
  padding: 15px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
}

textarea {
  flex-grow: 1;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 12px;
  resize: none;
  height: 60px;
  font-family: inherit;
  font-size: 14px;
}

button {
  margin-left: 10px;
  padding: 0 20px;
  background-color: #1976d2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:hover:not(:disabled) {
  background-color: #1565c0;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>
