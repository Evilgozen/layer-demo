<template>
  <div class="ai-assistant-container" :class="{ 'senior-mode': seniorMode }">
    <!-- 左侧历史记录面板 -->
    <div class="history-panel">
      <div class="history-header">
        <h3>历史记录</h3>
        <button @click="createNewConversation" class="new-chat-btn">新对话</button>
      </div>
      <div class="history-list">
        <div 
          v-for="(conversation, index) in conversations" 
          :key="index"
          :class="['history-item', currentConversationIndex === index ? 'active' : '']"
          @click="switchConversation(index)"
        >
          <div class="history-title">{{ getConversationTitle(conversation) }}</div>
          <div class="history-date">{{ formatDate(conversation.timestamp) }}</div>
        </div>
        <div v-if="conversations.length === 0" class="no-history">
          暂无历史记录
        </div>
      </div>
    </div>
    <div class="main-content">
    <div class="header">
      <h1>理工包青天</h1>
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
      
      <!-- 免责声明 -->
      <div class="disclaimer">
        <p><strong>免责声明：</strong>本系统提供的法律咨询仅供参考，不构成正式法律意见。具体案件请咨询专业律师。</p>
      </div>
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

// 对话历史记录
const conversations = ref([]);
const currentConversationIndex = ref(0);

// 当前对话消息
const messages = ref([
  { role: 'assistant', content: '您好！我是您的法律咨询助手。请问有什么法律问题我可以帮您解答？' }
]);
const loading = ref(false);
const messagesContainer = ref(null);

// 检查用户是否已登录并加载历史记录
onMounted(async () => {
  if (!userStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  
  if (!userStore.user) {
    await userStore.fetchUserData();
  }
  
  // 从本地存储加载对话历史
  loadConversations();
  
  // 如果没有历史记录，创建一个新对话
  if (conversations.value.length === 0) {
    createNewConversation();
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
    
    // 保存当前对话到历史记录
    saveCurrentConversation();
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

// 创建新对话
async function createNewConversation() {
  // 保存当前对话（如果有消息）
  if (messages.value.length > 1) {
    await saveCurrentConversation();
  }
  
  // 创建新对话
  messages.value = [
    { role: 'assistant', content: '您好！我是您的法律咨询助手。请问有什么法律问题我可以帮您解答？' }
  ];
  currentConversationIndex.value = conversations.value.length;
}

// 保存当前对话到后端数据库
async function saveCurrentConversation() {
  // 如果只有初始欢迎消息，不保存
  if (messages.value.length <= 1) return;
  
  try {
    // 准备要发送到后端的数据
    const conversationData = {
      messages: messages.value.map(msg => ({
        role: msg.role,
        content: msg.content
      })),
      title: getConversationTitle({ messages: messages.value })
    };
    
    let response;
    
    // 如果是更新现有对话
    if (currentConversationIndex.value < conversations.value.length) {
      const conversationId = conversations.value[currentConversationIndex.value].id;
      response = await axios.put(`http://localhost:8000/chat/conversations/${conversationId}`, 
        conversationData,
        {
          headers: {
            'Authorization': `Bearer ${userStore.token}`,
            'Content-Type': 'application/json'
          }
        }
      );
    } else {
      // 创建新对话
      response = await axios.post('http://localhost:8000/chat/conversations/', 
        conversationData,
        {
          headers: {
            'Authorization': `Bearer ${userStore.token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      // 添加新对话到列表
      const newConversation = {
        id: response.data.id.toString(),
        timestamp: response.data.created_at,
        messages: messages.value,
        title: response.data.title
      };
      
      conversations.value.push(newConversation);
      currentConversationIndex.value = conversations.value.length - 1;
    }
  } catch (error) {
    console.error('保存对话失败:', error);
  }
}

// 切换到指定对话
async function switchConversation(index) {
  // 保存当前对话
  if (messages.value.length > 1) {
    await saveCurrentConversation();
  }
  
  // 切换到选定的对话
  currentConversationIndex.value = index;
  
  try {
    // 从后端加载完整对话内容
    const conversationId = conversations.value[index].id;
    const response = await axios.get(`http://localhost:8000/chat/conversations/${conversationId}`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    // 更新消息列表
    if (response.data && response.data.messages) {
      messages.value = response.data.messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      // 生成对话标题
      let title = response.data.title;
      if (!title && messages.value.length > 0) {
        // 如果没有标题，尝试从消息中生成
        const userMessage = messages.value.find(msg => msg.role === 'user');
        if (userMessage) {
          title = userMessage.content.length > 20 
            ? userMessage.content.substring(0, 20) + '...' 
            : userMessage.content;
        } else {
          title = '对话 ' + new Date(response.data.created_at).toLocaleDateString();
        }
      }
      
      // 更新对话数据
      conversations.value[index] = {
        id: response.data.id.toString(),
        timestamp: response.data.created_at,
        messages: [...messages.value],
        title: title
      };
    }
  } catch (error) {
    console.error('加载对话内容失败:', error);
    // 如果加载失败，使用空消息列表
    messages.value = [
      { role: 'assistant', content: '您好！我是您的法律咨询助手。请问有什么法律问题我可以帮您解答？' }
    ];
  }
}

// 从后端加载对话历史
async function loadConversations() {
  try {
    const response = await axios.get('http://localhost:8000/chat/conversations/', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    if (response.data && Array.isArray(response.data)) {
      // 转换后端数据格式为前端格式
      conversations.value = response.data.map(conv => ({
        id: conv.id.toString(),
        timestamp: conv.created_at,
        messages: [],  // 初始只加载标题，消息内容会在切换对话时加载
        title: conv.title || '对话 ' + new Date(conv.created_at).toLocaleDateString()
      }));
    }
  } catch (error) {
    console.error('加载对话历史失败:', error);
    conversations.value = [];
  }
}

// 获取对话标题（使用第一条用户消息作为标题）
function getConversationTitle(conversation) {
  // 如果已有标题且不是默认的'新对话'，则使用现有标题
  if (conversation.title && conversation.title !== '新对话') {
    return conversation.title;
  }
  
  const userMessage = conversation.messages.find(msg => msg.role === 'user');
  if (userMessage) {
    // 截取前20个字符作为标题
    return userMessage.content.length > 20 
      ? userMessage.content.substring(0, 20) + '...' 
      : userMessage.content;
  }
  
  // 如果没有用户消息，使用日期作为标题
  if (conversation.timestamp) {
    return '对话 ' + new Date(conversation.timestamp).toLocaleDateString();
  }
  
  return '新对话';
}

// 格式化日期
function formatDate(dateString) {
  const date = new Date(dateString);
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
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
  height: 100vh;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0;
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

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 20px;
  box-sizing: border-box;
  overflow: hidden;
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

/* 历史记录面板样式 */
.history-panel {
  width: 280px;
  height: 100vh;
  background-color: #f0f2f5;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.history-header h3 {
  margin: 0;
  color: #333;
}

.new-chat-btn {
  background-color: #1976d2;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.new-chat-btn:hover {
  background-color: #1565c0;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.history-item {
  padding: 12px 15px;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
  border: 1px solid transparent;
}

.history-item:hover {
  background-color: #e8eaf6;
}

.history-item.active {
  background-color: #e3f2fd;
  border-color: #bbdefb;
}

.history-title {
  font-weight: 500;
  margin-bottom: 5px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-date {
  font-size: 12px;
  color: #666;
}

.no-history {
  text-align: center;
  color: #666;
  padding: 20px;
  font-style: italic;
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

/* 免责声明样式 */
.disclaimer {
  padding: 10px 15px;
  background-color: #f8f9fa;
  border-top: 1px solid #e0e0e0;
  font-size: 12px;
  color: #666;
  text-align: center;
}

.disclaimer p {
  margin: 0;
  line-height: 1.4;
}
</style>
