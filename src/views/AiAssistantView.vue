<template>
  <div class="ai-assistant-container" :class="{ 'senior-mode': seniorMode }">
    <!-- 移动端遮罩层 -->
    <div v-if="showHistoryPanel" class="mobile-overlay" @click="toggleHistoryPanel"></div>
    
    <!-- 左侧历史记录面板 -->
    <div class="history-panel" :class="{ 'mobile-open': showHistoryPanel }">
      <div class="history-header">
        <h3>历史记录</h3>
        <div class="history-controls">
          <button @click="createNewConversation" class="new-chat-btn">新对话</button>
          <button @click="toggleHistoryPanel" class="close-panel-btn mobile-only">×</button>
        </div>
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
      <div class="header-left">
        <button @click="toggleHistoryPanel" class="menu-btn mobile-only">☰</button>
        <h1>理工包青天</h1>
      </div>
      <div class="header-right">
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

// 移动端历史记录面板控制
const showHistoryPanel = ref(false);

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
  
  const userMessage = { role: 'user', content: userInput.value };
  messages.value.push(userMessage);
  
  // Add a placeholder for the assistant's response
  messages.value.push({ role: 'assistant', content: '' });
  
  const currentInput = userInput.value;
  userInput.value = ''; // Clear input field
  loading.value = true;

  // Prepare messages for the API (last few messages for context, or as per your backend logic)
  // For simplicity, sending all current messages. Adjust if needed.
  const apiMessages = messages.value.slice(0, -1).map(msg => ({ // Exclude the empty assistant message placeholder
    role: msg.role,
    content: msg.content
  }));
   // Add the current user input that triggered this call
  apiMessages.push({role: 'user', content: currentInput});

  try {
    const response = await fetch('http://localhost:8000/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userStore.token}` // Assuming token is stored in userStore
      },
      body: JSON.stringify({ messages: apiMessages })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
      const assistantMessageIndex = messages.value.length - 1;
      messages.value[assistantMessageIndex].content = `Error: ${errorData.detail || response.statusText}`;
      loading.value = false;
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const assistantMessageIndex = messages.value.length - 1;

    let done = false;
    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        messages.value[assistantMessageIndex].content += chunk;
        // Auto-scroll as content is added
        nextTick(() => {
          if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
          }
        });
      }
    }
    // Final decode for any remaining buffered data if stream ended abruptly
    // const finalChunk = decoder.decode(); 
    // if (finalChunk) { messages.value[assistantMessageIndex].content += finalChunk; }

  } catch (error) {
    console.error('Error sending message or processing stream:', error);
    const assistantMessageIndex = messages.value.length - 1;
    if (messages.value[assistantMessageIndex]) {
        messages.value[assistantMessageIndex].content = '抱歉，处理您的请求时发生错误。';
    }
  } finally {
    loading.value = false;
    saveCurrentConversation(); // Save after the full response is received
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
  
  // 移动端切换对话后关闭历史记录面板
  if (window.innerWidth <= 768) {
    showHistoryPanel.value = false;
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

// 切换移动端历史记录面板
function toggleHistoryPanel() {
  showHistoryPanel.value = !showHistoryPanel.value;
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

/* 老年模式样式 - 蓝白主题 */
.senior-mode {
  font-size: 140%;
  font-weight: 600;
  background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%);
  border: 3px solid #2196f3;
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(33, 150, 243, 0.2);
}

.senior-mode .ai-assistant-container {
  background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%);
}

.senior-mode button {
  font-size: 140%;
  font-weight: bold;
  padding: 16px 32px;
  border-radius: 12px;
  min-height: 56px;
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  border: none;
  color: white;
  box-shadow: 0 4px 16px rgba(33, 150, 243, 0.3);
  transition: all 0.3s ease;
}

.senior-mode button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(33, 150, 243, 0.4);
}

.senior-mode textarea {
  font-size: 140%;
  font-weight: 600;
  padding: 20px;
  border: 3px solid #2196f3;
  border-radius: 12px;
  min-height: 80px;
  background: #fff;
  box-shadow: inset 0 2px 8px rgba(33, 150, 243, 0.1);
}

.senior-mode .message-content {
  font-size: 140%;
  font-weight: 600;
  line-height: 1.8;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  border: 2px solid #2196f3;
  margin: 10px 0;
  color: #333 !important;
}

.senior-mode h1 {
  font-size: 200%;
  font-weight: 700;
  color: #2196f3;
  text-shadow: 2px 2px 4px rgba(33, 150, 243, 0.2);
}

.senior-mode .user-info span {
  font-size: 140%;
  font-weight: 600;
  color: #2196f3;
}

.senior-mode .history-item {
  font-size: 120%;
  font-weight: 600;
  padding: 16px 20px;
  border: 2px solid #2196f3;
  background: #fff;
  margin-bottom: 12px;
}

.senior-mode .history-item:hover {
  background: #e3f2fd;
  transform: translateX(5px);
}

.senior-mode .history-item.active {
  background: #2196f3;
  color: white;
}

.senior-mode .chat-input {
  border: 3px solid #2196f3;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
}

.senior-mode .send-button {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  font-size: 140%;
  padding: 16px 24px;
  min-width: 120px;
}

.senior-mode .new-chat-btn {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  font-size: 120%;
  padding: 12px 20px;
  min-height: 48px;
}

.senior-mode .logout-btn {
  font-size: 120%;
  padding: 12px 20px;
  border: 3px solid #2196f3;
  background: #fff;
  color: #2196f3;
  font-weight: 600;
}

.senior-mode .logout-btn:hover {
  background: #2196f3;
  color: white;
  transform: translateY(-2px);
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
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
  padding: 12px 20px;
  border-radius: 25px;
  border: 3px solid #2196f3;
  box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
  transition: all 0.3s ease;
  margin-left: 20px;
}

.senior-mode-toggle:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(33, 150, 243, 0.4);
}

.senior-mode-toggle input {
  margin-right: 12px;
  width: 24px;
  height: 24px;
  cursor: pointer;
  accent-color: #fff;
}

.toggle-label {
  color: white;
  font-weight: 700;
  font-size: 16px;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
}

.senior-mode .senior-mode-toggle {
  background: linear-gradient(135deg, #1976d2 0%, #0d47a1 100%);
  border-color: #1976d2;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 4px 15px rgba(25, 118, 210, 0.3);
  }
  50% {
    box-shadow: 0 8px 25px rgba(25, 118, 210, 0.5);
  }
  100% {
    box-shadow: 0 4px 15px rgba(25, 118, 210, 0.3);
  }
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
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

/* 历史记录面板样式 */
.history-panel {
  width: 300px;
  height: 100vh;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-right: 1px solid rgba(224, 224, 224, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(10px);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid rgba(224, 224, 224, 0.3);
  background: rgba(255, 255, 255, 0.5);
}

.history-header h3 {
  margin: 0;
  color: #333;
  font-weight: 600;
  font-size: 18px;
}

.new-chat-btn {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(25, 118, 210, 0.4);
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.history-item {
  padding: 16px 18px;
  border-radius: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(5px);
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.history-item.active {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-color: #2196f3;
  box-shadow: 0 4px 16px rgba(33, 150, 243, 0.2);
  transform: translateX(8px);
}

.history-title {
  font-weight: 600;
  margin-bottom: 5px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 15px;
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

/* 移动端响应式样式 */
@media (max-width: 768px) {
  .ai-assistant-container {
    height: 100vh;
    max-width: 100%;
    padding: 0;
  }

  /* 移动端遮罩层 */
  .mobile-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 998;
    display: block;
  }

  /* 历史记录面板移动端样式 */
  .history-panel {
    position: fixed;
    top: 0;
    left: -100%;
    width: 80%;
    max-width: 320px;
    height: 100vh;
    z-index: 999;
    transition: left 0.3s ease;
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  }

  .history-panel.mobile-open {
    left: 0;
  }

  /* 历史记录头部控制按钮 */
  .history-controls {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .close-panel-btn {
    background: #f44336;
    color: white;
    border: none;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 18px;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
  }

  .close-panel-btn:hover {
    background: #d32f2f;
    transform: scale(1.1);
  }

  /* 主内容区域 */
  .main-content {
    width: 100%;
    height: 100vh;
    padding: 10px;
  }

  /* 头部样式 */
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    margin-bottom: 10px;
    flex-wrap: nowrap;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .header h1 {
    font-size: 20px;
    margin: 0;
  }

  /* 移动端菜单按钮 */
  .menu-btn {
    background: #2196f3;
    color: white;
    border: none;
    width: 40px;
    height: 40px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
  }

  .menu-btn:hover {
    background: #1976d2;
    transform: scale(1.05);
  }

  /* 显示/隐藏移动端专用元素 */
  .mobile-only {
    display: block;
  }

  /* 老年模式切换按钮移动端优化 */
  .senior-mode-toggle {
    padding: 8px 12px;
    font-size: 14px;
  }

  .senior-mode-toggle input {
    width: 18px;
    height: 18px;
    margin-right: 8px;
  }

  .toggle-label {
    font-size: 14px;
  }

  /* 用户信息移动端优化 */
  .user-info {
    flex-direction: column;
    gap: 5px;
    align-items: flex-end;
  }

  .user-info span {
    font-size: 12px;
  }

  .logout-btn {
    padding: 4px 8px;
    font-size: 12px;
  }

  /* 聊天容器移动端优化 */
  .chat-container {
    height: calc(100vh - 80px);
    border-radius: 15px;
  }

  .chat-messages {
    padding: 15px;
    max-height: calc(100vh - 200px);
  }

  .message {
    max-width: 90%;
    padding: 10px 12px;
    font-size: 14px;
  }

  /* 聊天输入框移动端优化 */
  .chat-input {
    padding: 10px;
    flex-direction: column;
    gap: 10px;
  }

  .chat-input textarea {
    width: 100%;
    height: 80px;
    font-size: 16px;
    border-radius: 8px;
  }

  .chat-input button {
    width: 100%;
    height: 44px;
    font-size: 16px;
    border-radius: 8px;
    margin-left: 0;
  }

  /* 免责声明移动端优化 */
  .disclaimer {
    padding: 8px 10px;
    font-size: 11px;
  }

  /* 老年模式移动端优化 */
  .senior-mode .header h1 {
    font-size: 24px;
  }

  .senior-mode .menu-btn {
    width: 48px;
    height: 48px;
    font-size: 20px;
  }

  .senior-mode .message {
    font-size: 18px;
    padding: 16px;
  }

  .senior-mode .chat-input textarea {
    font-size: 18px;
    height: 100px;
  }

  .senior-mode .chat-input button {
    height: 56px;
    font-size: 18px;
  }
}

/* 430px宽度特别优化 */
@media (max-width: 430px) {
  .header {
    padding: 8px 0;
  }

  .header h1 {
    font-size: 18px;
  }

  .menu-btn {
    width: 36px;
    height: 36px;
    font-size: 16px;
  }

  .senior-mode-toggle {
    padding: 6px 10px;
    font-size: 12px;
  }

  .senior-mode-toggle input {
    width: 16px;
    height: 16px;
  }

  .toggle-label {
    font-size: 12px;
  }

  .user-info span {
    font-size: 11px;
  }

  .logout-btn {
    padding: 3px 6px;
    font-size: 11px;
  }

  .chat-messages {
    padding: 10px;
  }

  .message {
    font-size: 13px;
    padding: 8px 10px;
  }

  .chat-input {
    padding: 8px;
  }

  .chat-input textarea {
    height: 70px;
    font-size: 14px;
  }

  .chat-input button {
    height: 40px;
    font-size: 14px;
  }

  /* 老年模式430px优化 */
  .senior-mode .header h1 {
    font-size: 20px;
  }

  .senior-mode .menu-btn {
    width: 44px;
    height: 44px;
    font-size: 18px;
  }

  .senior-mode .message {
    font-size: 16px;
    padding: 12px;
  }

  .senior-mode .chat-input textarea {
    font-size: 16px;
    height: 90px;
  }

  .senior-mode .chat-input button {
    height: 50px;
    font-size: 16px;
  }
}

/* 桌面端隐藏移动端专用元素 */
@media (min-width: 769px) {
  .mobile-only {
    display: none;
  }

  .mobile-overlay {
    display: none;
  }

  .history-controls {
    display: block;
  }

  .header-left {
    display: block;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 20px;
  }
}
</style>
