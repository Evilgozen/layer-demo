<template>
  <div class="discussion-detail-container">
    <div class="header">
      <h1>讨论详情</h1>
      <div class="user-info" v-if="userStore.user">
        <span>欢迎, {{ userStore.user.username }}</span>
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </div>

    <!-- 讨论详情 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!discussion" class="no-results">
      <p>未找到讨论详情</p>
    </div>
    <div v-else class="discussion-detail">
      <div class="discussion-header">
        <h2>{{ discussion.title }}</h2>
        <span class="discussion-date">{{ formatDate(discussion.created_at) }}</span>
      </div>
      <div class="discussion-author">发起人: {{ discussion.username }}</div>
      <div class="discussion-content">{{ discussion.content }}</div>

      <!-- 相关法条（如果有） -->
      <div v-if="relatedArticle" class="related-article">
        <h3>相关法条</h3>
        <div class="article-card">
          <div class="article-header">
            <h4>{{ relatedArticle.title }}</h4>
            <span class="article-number">{{ relatedArticle.article_number }}</span>
          </div>
          <div class="article-source">{{ relatedArticle.source }}</div>
          <div class="article-content">{{ relatedArticle.content }}</div>
          <div class="article-footer">
            <span class="article-category">{{ relatedArticle.category }}</span>
            <button @click="viewArticleDetail(relatedArticle.id)" class="view-article-btn">
              查看法条详情
            </button>
          </div>
        </div>
      </div>

      <!-- 评论区 -->
      <div class="comments-section">
        <h3>评论 ({{ totalItems }})</h3>
        
        <!-- 添加评论表单 -->
        <div class="add-comment-form">
          <textarea 
            v-model="newComment.content" 
            placeholder="请输入您的评论"
            rows="3"
          ></textarea>
          <button @click="submitComment" :disabled="isSubmitting" class="submit-btn">
            {{ isSubmitting ? '提交中...' : '提交评论' }}
          </button>
        </div>

        <!-- 评论列表 -->
        <div v-if="loadingComments" class="loading">加载评论中...</div>
        <div v-else-if="comments.length === 0" class="no-results">
          <p>暂无评论，快来发表第一条评论吧！</p>
        </div>
        <div v-else class="comments-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-header">
              <span class="comment-author">{{ comment.username }}</span>
              <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
            </div>
            <div class="comment-content">{{ comment.content }}</div>
          </div>
        </div>

        <!-- 分页控制 -->
        <div class="pagination" v-if="comments.length > 0">
          <button 
            @click="prevPage" 
            :disabled="currentPage === 1"
            class="pagination-btn"
          >
            上一页
          </button>
          <div class="page-selector">
            <span>第</span>
            <select v-model="currentPage" @change="fetchComments">
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

      <!-- 返回按钮 -->
      <div class="actions">
        <button @click="goBack" class="back-btn">返回讨论列表</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useUserStore } from '../stores/userStore';
import { useRouter, useRoute } from 'vue-router';

const userStore = useUserStore();
const router = useRouter();
const route = useRoute();

// 获取讨论ID
const discussionId = computed(() => parseInt(route.params.id));

// 讨论详情
const discussion = ref(null);
const relatedArticle = ref(null);
const loading = ref(true);

// 评论数据
const comments = ref([]);
const loadingComments = ref(false);

// 分页参数
const currentPage = ref(1);
const pageSize = ref(5);
const totalItems = ref(0);
const totalPages = ref(100); // 假设有100页

// 新评论
const newComment = ref({
  content: ''
});
const isSubmitting = ref(false);

// 初始化加载
onMounted(async () => {
  if (!userStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  
  await fetchDiscussionDetail();
  await fetchComments();
});

// 导入模拟数据
import mockDiscussionDetail from '../assets/mock-data/discussion-detail.json';
import mockComments from '../assets/mock-data/discussion-comments.json';
import mockLegalArticles from '../assets/mock-data/legal-articles.json';

// 获取讨论详情
async function fetchDiscussionDetail() {
  loading.value = true;
  
  try {
    // 使用模拟数据
    discussion.value = mockDiscussionDetail;
    
    // 如果有关联的法条，获取法条信息
    if (discussion.value.legal_article_id) {
      await fetchRelatedArticle(discussion.value.legal_article_id);
    }
  } catch (error) {
    console.error('Error fetching discussion detail:', error);
  } finally {
    loading.value = false;
  }
}

// 获取关联法条
async function fetchRelatedArticle(articleId) {
  try {
    // 使用模拟数据
    const article = mockLegalArticles.find(article => article.id === articleId);
    if (article) {
      relatedArticle.value = article;
    }
  } catch (error) {
    console.error('Error fetching related article:', error);
  }
}

// 获取评论
async function fetchComments() {
  loadingComments.value = true;
  
  try {
    // 使用模拟数据
    // 计算总数量
    totalItems.value = mockComments.length;
    
    // 分页处理 - 只显示前两页的数据，其他页显示空
    if (currentPage.value <= 2) {
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      comments.value = mockComments.slice(start, end);
    } else {
      // 第3页及以后显示空数据
      comments.value = [];
    }
  } catch (error) {
    console.error('Error fetching comments:', error);
  } finally {
    loadingComments.value = false;
  }
}

// 提交评论
async function submitComment() {
  if (!newComment.value.content.trim()) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    // 模拟提交评论
    const newId = mockComments.length > 0 ? Math.max(...mockComments.map(c => c.id)) + 1 : 1;
    
    const newCommentItem = {
      id: newId,
      content: newComment.value.content,
      user_id: 1, // 假设当前用户ID为1
      username: userStore.user ? userStore.user.username : 'demo_user',
      discussion_id: discussionId.value,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    // 将新评论添加到模拟数据中
    mockComments.unshift(newCommentItem);
    
    // 重置表单
    newComment.value.content = '';
    
    // 刷新评论列表
    await fetchComments();
    
    // 更新讨论中的评论数
    if (discussion.value) {
      discussion.value.comments_count = (discussion.value.comments_count || 0) + 1;
    }
  } catch (error) {
    console.error('Error submitting comment:', error);
    alert('评论提交失败，请稍后再试');
  } finally {
    isSubmitting.value = false;
  }
}

// 分页控制
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    fetchComments();
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    fetchComments();
  }
}

// 查看法条详情
function viewArticleDetail(articleId) {
  router.push(`/legal-article/${articleId}`);
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

// 返回讨论列表
function goBack() {
  router.back();
}

// 退出登录
function logout() {
  userStore.logout();
  router.push('/login');
}
</script>

<style scoped>
.discussion-detail-container {
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

.discussion-detail {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.discussion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.discussion-header h2 {
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
  margin-bottom: 20px;
  line-height: 1.6;
  color: #333;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 8px;
  border-left: 4px solid #2196F3;
}

.related-article {
  background-color: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
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

.article-header h4 {
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

.view-article-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}

.comments-section {
  margin-top: 30px;
}

.add-comment-form {
  margin-bottom: 20px;
}

.add-comment-form textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
  margin-bottom: 10px;
  resize: vertical;
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

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.comment-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.comment-author {
  font-weight: bold;
  color: #333;
}

.comment-date {
  color: #666;
  font-size: 0.9em;
}

.comment-content {
  line-height: 1.5;
  color: #333;
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

.actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-start;
}

.back-btn {
  background-color: #607D8B;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.loading, .no-results {
  text-align: center;
  padding: 20px;
  color: #666;
}
</style>