<template>
  <div class="ai-assistant-container">
    <a-card class="ai-assistant-card" title="理工包青天 - 法律AI助手">
      <a-typography-title level="3" class="assistant-title">个人法律助手</a-typography-title>
      
      <div class="chat-container">
        <div class="chat-messages" ref="chatMessagesRef">
          <div v-for="(message, index) in messages" :key="index" :class="['message', message.role]">
            <div class="message-content">
              <div v-if="message.role === 'assistant'" class="assistant-avatar">AI</div>
              <div v-else class="user-avatar">您</div>
              <div class="message-text" v-html="formatMessage(message.content)"></div>
            </div>
          </div>
          <div v-if="loading" class="message assistant">
            <div class="message-content">
              <div class="assistant-avatar">AI</div>
              <div class="message-text typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="prompt-templates" v-if="showPromptTemplates">
          <a-typography-title level="5">常用提示词模板</a-typography-title>
          <a-row :gutter="[16, 16]">
            <a-col :span="8" v-for="(template, index) in promptTemplates" :key="index">
              <a-card hoverable @click="applyTemplate(template.prompt)" class="prompt-card">
                <a-typography-title level="5">{{ template.title }}</a-typography-title>
                <p>{{ template.description }}</p>
              </a-card>
            </a-col>
          </a-row>
        </div>
        
        <div class="input-container">
          <a-button 
            class="template-toggle" 
            type="link" 
            @click="showPromptTemplates = !showPromptTemplates"
          >
            {{ showPromptTemplates ? '隐藏模板' : '显示模板' }}
          </a-button>
          
          <a-textarea
            v-model:value="userInput"
            placeholder="请输入您的法律问题..."
            :rows="3"
            :disabled="loading"
            @keydown.enter.ctrl="sendMessage"
          />
          
          <div class="button-container">
            <a-button 
              type="primary" 
              :loading="loading" 
              @click="sendMessage" 
              :disabled="!userInput.trim()"
            >
              发送
            </a-button>
            <a-button @click="clearChat">清空对话</a-button>
          </div>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'
import { message } from 'ant-design-vue'
import { useUserStore } from '../stores/userStore'
import * as marked from 'marked'
import DOMPurify from 'dompurify'

const userStore = useUserStore()
const userInput = ref('')
const messages = ref([
  {
    role: 'assistant',
    content: '您好！我是您的法律AI助手。请问有什么法律问题我可以帮您解答？'
  }
])
const loading = ref(false)
const chatMessagesRef = ref(null)
const showPromptTemplates = ref(false)

// 预设的提示词模板
const promptTemplates = [
  {
    title: '合同审查',
    description: '分析合同条款中的潜在风险',
    prompt: '请帮我分析以下合同条款中可能存在的法律风险和不公平条款：[粘贴合同条款]'
  },
  {
    title: '法律咨询',
    description: '针对具体法律问题的咨询',
    prompt: '根据中国法律，[描述您的具体情况]，我有什么权利和可能的解决方案？'
  },
  {
    title: '案例分析',
    description: '分析特定案例的法律依据',
    prompt: '请分析以下案例的法律依据和可能的判决结果：[描述案例]'
  },
  {
    title: '法律文书',
    description: '生成法律文书模板',
    prompt: '请帮我起草一份[文书类型]，情况如下：[描述具体情况]'
  },
  {
    title: '法规解读',
    description: '解读特定法律法规',
    prompt: '请解读[法律法规名称]中关于[具体条款]的具体含义和适用范围。'
  },
  {
    title: '权益保障',
    description: '了解自身权益保障措施',
    prompt: '作为[身份]，在[具体情境]下，我的权益受到了侵害，我应该如何保护自己的合法权益？'
  }
]

// 发送消息到DeepSeek API
const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return
  
  const userMessage = userInput.value.trim()
  messages.value.push({ role: 'user', content: userMessage })
  userInput.value = ''
  loading.value = true
  
  scrollToBottom()
  
  try {
    // 构建发送给DeepSeek API的消息历史
    const messageHistory = messages.value.map(msg => ({
      role: msg.role,
      content: msg.content
    }))
    
    // 调用后端API，后端将转发请求到DeepSeek API
    const response = await axios.post('http://localhost:8000/ai/chat', {
      messages: messageHistory,
      model: 'deepseek-chat', // 或其他DeepSeek模型ID
      temperature: 0.7,
      max_tokens: 2000
    }, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    // 添加AI回复到消息列表
    messages.value.push({
      role: 'assistant',
      content: response.data.response || '抱歉，我无法处理您的请求。'
    })
  } catch (error) {
    console.error('Error sending message to AI:', error)
    message.error('发送消息失败，请稍后再试')
    
    // 添加错误消息
    messages.value.push({
      role: 'assistant',
      content: '抱歉，发生了错误。请检查网络连接或稍后再试。'
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

// 应用提示词模板
const applyTemplate = (templateText) => {
  userInput.value = templateText
  showPromptTemplates.value = false
}

// 清空对话
const clearChat = () => {
  messages.value = [
    {
      role: 'assistant',
      content: '您好！我是您的法律AI助手。请问有什么法律问题我可以帮您解答？'
    }
  ]
}

// 格式化消息内容，支持Markdown
const formatMessage = (content) => {
  // 使用marked将Markdown转换为HTML，并使用DOMPurify清理HTML
  return DOMPurify.sanitize(marked.parse(content))
}

// 滚动到聊天窗口底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  scrollToBottom()
})

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.ai-assistant-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  padding: 20px;
}

.ai-assistant-card {
  width: 100%;
  height: 100%;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border-radius: 8px;
}

.assistant-title {
  text-align: center;
  margin-bottom: 20px;
  color: #1890ff;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 8px;
  margin-bottom: 20px;
  max-height: calc(100vh - 350px);
}

.message {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}

.message-content {
  display: flex;
  max-width: 80%;
}

.user {
  align-items: flex-end;
  align-self: flex-end;
}

.assistant {
  align-items: flex-start;
  align-self: flex-start;
}

.user .message-content {
  flex-direction: row-reverse;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  margin: 0 8px;
  line-height: 1.5;
}

.user .message-text {
  background-color: #1890ff;
  color: white;
  border-top-right-radius: 2px;
}

.assistant .message-text {
  background-color: #f0f2f5;
  color: #333;
  border-top-left-radius: 2px;
}

.user-avatar, .assistant-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.user-avatar {
  background-color: #1890ff;
  color: white;
}

.assistant-avatar {
  background-color: #52c41a;
  color: white;
}

.input-container {
  margin-top: auto;
  display: flex;
  flex-direction: column;
}

.button-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  gap: 10px;
}

.prompt-templates {
  margin-bottom: 20px;
  background-color: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
}

.prompt-card {
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
}

.prompt-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.template-toggle {
  align-self: flex-start;
  margin-bottom: 10px;
}

/* 打字指示器动画 */
.typing-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  margin: 0 2px;
  background-color: #8c8c8c;
  border-radius: 50%;
  display: inline-block;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.5);
  }
  100% {
    transform: scale(1);
  }
}

/* 消息内容中的Markdown样式 */
.message-text :deep(a) {
  color: #1890ff;
  text-decoration: none;
}

.message-text :deep(pre) {
  background-color: #f0f2f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.message-text :deep(code) {
  background-color: rgba(0, 0, 0, 0.06);
  padding: 2px 4px;
  border-radius: 3px;
}

.message-text :deep(ul), .message-text :deep(ol) {
  padding-left: 20px;
}

.message-text :deep(blockquote) {
  border-left: 4px solid #ddd;
  padding-left: 16px;
  margin-left: 0;
  color: #666;
}

.assistant .message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0;
}

.assistant .message-text :deep(th), .assistant .message-text :deep(td) {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.assistant .message-text :deep(th) {
  background-color: #f0f2f5;
}
</style>
