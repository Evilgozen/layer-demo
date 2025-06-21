<template>
  <div class="discussions-container" :class="{ 'senior-mode': seniorMode }">
    <div class="header">
      <h1>法律讨论区</h1>
      <div class="header-controls">
        <div class="senior-mode-toggle" @click="toggleSeniorMode">
          <input type="checkbox" v-model="seniorMode" />
          <span class="toggle-label">老年模式</span>
        </div>
        <div class="user-info" v-if="userStore.user">
          <span>欢迎, {{ userStore.user.username }}</span>
          <button @click="logout" class="logout-btn">退出登录</button>
        </div>
      </div>
    </div>

    <!-- 法条信息（如果有关联的法条） -->
    <div v-if="relatedArticle" class="related-article">
      <h2>相关法条</h2>
      <div class="article-card">
        <div class="article-header">
          <h3>{{ relatedArticle.title }}</h3>
          <span class="article-number">{{ relatedArticle.article_number }}</span>
        </div>
        <div class="article-source">{{ relatedArticle.source }}</div>
        <div class="article-content">{{ relatedArticle.content }}</div>
        <div class="article-footer">
          <span class="article-category">{{ relatedArticle.category }}</span>
        </div>
      </div>
    </div>

    <!-- 讨论列表 -->
    <div class="discussions-section">
      <div class="section-header">
        <h2>讨论列表</h2>
        <button @click="showNewDiscussionForm = true" class="new-discussion-btn">
          发起新讨论
        </button>
      </div>

      <!-- 新讨论表单 -->
      <div v-if="showNewDiscussionForm" class="new-discussion-form">
        <h3>发起新讨论</h3>
        <div class="form-group">
          <label for="title">标题</label>
          <input 
            id="title" 
            v-model="newDiscussion.title" 
            type="text" 
            placeholder="请输入讨论标题"
          />
        </div>
        <div class="form-group">
          <label for="content">内容</label>
          <textarea 
            id="content" 
            v-model="newDiscussion.content" 
            placeholder="请输入讨论内容"
            rows="5"
          ></textarea>
        </div>
        <div class="form-actions">
          <button @click="cancelNewDiscussion" class="cancel-btn">取消</button>
          <button @click="createDiscussion" :disabled="isSubmitting" class="submit-btn">
            {{ isSubmitting ? '提交中...' : '提交' }}
          </button>
        </div>
      </div>

      <!-- 讨论列表 -->
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="discussions.length === 0" class="no-results">
        <p>暂无讨论，快来发起第一个讨论吧！</p>
      </div>
      <div v-else class="discussion-cards">
        <div v-for="discussion in discussions" :key="discussion.id" class="discussion-card">
          <div class="discussion-header">
            <h3>{{ discussion.title }}</h3>
            <span class="discussion-date">{{ formatDate(discussion.created_at) }}</span>
          </div>
          <div class="discussion-author">发起人: {{ discussion.username }}</div>
          <div class="discussion-content">{{ discussion.content }}</div>
          <div class="discussion-footer">
            <span class="comments-count">{{ discussion.comments_count }} 条评论</span>
            <button @click="viewDiscussionMock(discussion.id)" class="view-detail-btn">
              查看详情
            </button>
          </div>
        </div>
      </div>

      <!-- 分页控制 -->
      <div class="pagination" v-if="discussions.length > 0 || currentPage > 2">
        <button 
          @click="prevPage" 
          :disabled="currentPage === 1"
          class="pagination-btn"
        >
          上一页
        </button>
        <div class="page-selector">
          <span>第</span>
          <select v-model="currentPage" @change="fetchDiscussions">
            <option v-for="page in 100" :key="page" :value="page">{{ page }}</option>
          </select>
          <span>页 / 共 100 页</span>
        </div>
        <button 
          @click="nextPage" 
          :disabled="currentPage >= 100"
          class="pagination-btn"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useUserStore } from '../stores/userStore';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';

const userStore = useUserStore();
const router = useRouter();
const route = useRoute();

// 获取URL参数中的法条ID
const articleId = computed(() => route.query.articleId ? parseInt(route.query.articleId) : null);

// 相关法条信息
const relatedArticle = ref(null);

// 讨论列表数据
const discussions = ref([]);
const loading = ref(false);

// 分页参数
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);
// 显示100页，但实际只有前两页有数据
const totalPages = ref(100);

// 新讨论表单
const showNewDiscussionForm = ref(false);
const newDiscussion = ref({
  title: '',
  content: '',
  legal_article_id: null
});
const isSubmitting = ref(false);

// 老年模式
const seniorMode = ref(false);

// 切换老年模式
function toggleSeniorMode() {
  seniorMode.value = !seniorMode.value;
}

// 初始化加载
onMounted(async () => {
  if (!userStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  
  // 如果有法条ID，先获取法条信息
  if (articleId.value) {
    await fetchArticle();
    newDiscussion.value.legal_article_id = articleId.value;
  }
  
  // 获取讨论列表
  await fetchDiscussions();
});

// 导入模拟数据
import mockLegalArticles from '../assets/mock-data/legal-articles.json';
import mockDiscussions from '../assets/mock-data/discussions.json';

// 获取法条信息
async function fetchArticle() {
  try {
    // 使用模拟数据而不是API请求
    const article = mockLegalArticles.find(article => article.id === articleId.value);
    if (article) {
      relatedArticle.value = article;
    }
  } catch (error) {
    console.error('Error fetching mock legal article:', error);
    // 处理错误
  }
}

// 获取讨论列表
async function fetchDiscussions() {
  loading.value = true;
  
  try {
    // 使用模拟数据而不是API请求
    let filteredDiscussions = [...mockDiscussions];
    
    // 如果有法条ID，进行过滤
    if (articleId.value) {
      filteredDiscussions = filteredDiscussions.filter(
        discussion => discussion.legal_article_id === articleId.value
      );
    }
    
    // 计算总数量
    totalItems.value = filteredDiscussions.length;
    
    // 分页处理 - 只显示前两页的数据，其他页显示空
    if (currentPage.value <= 2) {
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      discussions.value = filteredDiscussions.slice(start, end);
    } else {
      // 第3页及以后显示空数据
      discussions.value = [];
    }
    
    console.log('使用模拟讨论数据：', discussions.value);
  } catch (error) {
    console.error('Error fetching discussions:', error);
    // 处理错误
  } finally {
    loading.value = false;
  }
}

// 分页控制
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    fetchDiscussions();
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    fetchDiscussions();
  }
}

// 创建新讨论
async function createDiscussion() {
  if (!newDiscussion.value.title || !newDiscussion.value.content) {
    alert('请填写完整的讨论信息');
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    // 使用模拟数据创建新讨论
    const newId = mockDiscussions.length > 0 ? Math.max(...mockDiscussions.map(d => d.id)) + 1 : 1;
    
    const newDiscussionItem = {
      id: newId,
      title: newDiscussion.value.title,
      content: newDiscussion.value.content,
      legal_article_id: newDiscussion.value.legal_article_id,
      user_id: 1, // 假设当前用户ID为1
      username: userStore.user ? userStore.user.username : 'demo_user',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      comments_count: 0
    };
    
    // 将新讨论添加到模拟数据中
    mockDiscussions.unshift(newDiscussionItem);
    
    // 重置表单
    showNewDiscussionForm.value = false;
    newDiscussion.value = {
      title: '',
      content: '',
      legal_article_id: articleId.value
    };
    
    // 刷新讨论列表
    await fetchDiscussions();
    
    // 显示成功消息
    alert('讨论创建成功！');
  } catch (error) {
    console.error('Error creating discussion:', error);
    alert('创建讨论失败，请稍后再试');
  } finally {
    isSubmitting.value = false;
  }
}

// 取消创建新讨论
function cancelNewDiscussion() {
  showNewDiscussionForm.value = false;
  newDiscussion.value = {
    title: '',
    content: '',
    legal_article_id: articleId.value
  };
}

// 查看讨论详情
function viewDiscussionDetail(discussionId) {
  router.push(`/discussion/${discussionId}`);
}

// 查看模拟讨论详情
function viewDiscussionMock(discussionId) {
  router.push(`/discussion-mock/${discussionId}`);
}

// 格式化日期
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// 退出登录
function logout() {
  userStore.logout();
  router.push('/login');
}
</script>

<style scoped>
.discussions-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
  color: #333;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logout-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

/* 老年模式切换按钮 */
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

.related-article {
  background-color: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.article-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.article-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.article-header h3 {
  margin: 0;
  color: #333;
}

.article-number {
  color: #666;
  font-size: 0.9em;
}

.article-source {
  color: #666;
  font-size: 0.9em;
  margin-bottom: 10px;
}

.article-content {
  margin-bottom: 15px;
  line-height: 1.5;
  color: #333;
}

.article-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.article-category {
  background-color: #e0e0e0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
}

.discussions-section {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  margin: 0;
  color: #333;
}

.new-discussion-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.new-discussion-form {
  background-color: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input, .form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-btn {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.loading, .no-results {
  text-align: center;
  padding: 20px;
  color: #666;
}

.discussion-cards {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.discussion-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.discussion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.discussion-header h3 {
  margin: 0;
  color: #333;
}

.discussion-date {
  color: #666;
  font-size: 0.9em;
}

.discussion-author {
  color: #666;
  font-size: 0.9em;
  margin-bottom: 10px;
}

.discussion-content {
  margin-bottom: 15px;
  line-height: 1.5;
  color: #333;
}

.discussion-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.discussion-actions {
  display: flex;
  gap: 10px;
}

.comments-count {
  color: #666;
  font-size: 0.9em;
}

.view-detail-btn {
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.view-mock-btn {
  background-color: #9C27B0;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 20px;
  gap: 10px;
}

.pagination-btn {
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.pagination-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.page-info {
  color: #666;
}

.page-selector {
  display: flex;
  align-items: center;
  gap: 5px;
}

.page-selector select {
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
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

.senior-mode h1 {
  font-size: 200%;
  font-weight: 700;
  color: #2196f3;
  text-shadow: 2px 2px 4px rgba(33, 150, 243, 0.2);
}

.senior-mode h2 {
  font-size: 180%;
  font-weight: 700;
  color: #2196f3;
}

.senior-mode h3 {
  font-size: 160%;
  font-weight: 600;
  color: #2196f3;
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

.senior-mode input, .senior-mode textarea {
  font-size: 140%;
  font-weight: 600;
  padding: 20px;
  border: 3px solid #2196f3;
  border-radius: 12px;
  background: #fff;
  box-shadow: inset 0 2px 8px rgba(33, 150, 243, 0.1);
}

.senior-mode .discussion-card {
  border: 3px solid #2196f3;
  background: #fff;
  padding: 24px;
  margin-bottom: 20px;
  border-radius: 15px;
  box-shadow: 0 8px 24px rgba(33, 150, 243, 0.1);
}

.senior-mode .article-card {
  border: 3px solid #2196f3;
  background: #fff;
  padding: 24px;
  border-radius: 15px;
  box-shadow: 0 8px 24px rgba(33, 150, 243, 0.1);
}

.senior-mode .new-discussion-form {
  background: #e3f2fd;
  border: 3px solid #2196f3;
  padding: 24px;
  border-radius: 15px;
}

.senior-mode .discussions-section {
  background: #fff;
  border: 3px solid #2196f3;
  padding: 24px;
  border-radius: 15px;
  box-shadow: 0 8px 24px rgba(33, 150, 243, 0.1);
}

.senior-mode .related-article {
  background: #e3f2fd;
  border: 3px solid #2196f3;
  padding: 24px;
  border-radius: 15px;
}

.senior-mode .user-info span {
  font-size: 140%;
  font-weight: 600;
  color: #2196f3;
}

.senior-mode .logout-btn {
  background: #fff;
  color: #2196f3;
  border: 3px solid #2196f3;
  font-weight: 600;
}

.senior-mode .logout-btn:hover {
  background: #2196f3;
  color: white;
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
</style>