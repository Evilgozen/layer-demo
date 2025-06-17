<template>
  <div class="discussions-container">
    <div class="header">
      <h1>法律讨论区</h1>
      <div class="user-info" v-if="userStore.user">
        <span>欢迎, {{ userStore.user.username }}</span>
        <button @click="logout" class="logout-btn">退出登录</button>
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
            <button @click="viewDiscussionDetail(discussion.id)" class="view-detail-btn">
              查看详情
            </button>
          </div>
        </div>
      </div>

      <!-- 分页控制 -->
      <div class="pagination" v-if="discussions.length > 0">
        <button 
          @click="prevPage" 
          :disabled="currentPage === 1"
          class="pagination-btn"
        >
          上一页
        </button>
        <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        <button 
          @click="nextPage" 
          :disabled="currentPage === totalPages"
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
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value));

// 新讨论表单
const showNewDiscussionForm = ref(false);
const newDiscussion = ref({
  title: '',
  content: '',
  legal_article_id: null
});
const isSubmitting = ref(false);

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
    
    // 分页处理
    const start = (currentPage.value - 1) * pageSize.value;
    const end = start + pageSize.value;
    discussions.value = filteredDiscussions.slice(start, end);
    
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
</style>