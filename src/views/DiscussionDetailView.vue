<template>
  <div class="discussion-detail-container">
    <div class="header">
      <button @click="goBack" class="back-btn">
        <span class="back-icon">←</span> 返回讨论列表
      </button>
      <div class="user-info" v-if="userStore.user">
        <span>欢迎, {{ userStore.user.username }}</span>
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </div>

    <!-- 讨论详情 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="discussion" class="discussion-detail">
      <div class="discussion-header">
        <h1>{{ discussion.title }}</h1>
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
          </div>
        </div>
      </div>

      <!-- 评论区 -->
      <div class="comments-section">
        <h2>评论区 ({{ comments.length }})</h2>
        
        <!-- 添加评论表单 -->
        <div class="new-comment-form">
          <h3>发表评论</h3>
          <div class="form-group">
            <textarea 
              v-model="newComment.content" 
              placeholder="请输入您的评论"
              rows="3"
            ></textarea>
          </div>
          <div class="form-actions">
            <button 
              @click="submitComment" 
              :disabled="isSubmitting || !newComment.content.trim()" 
              class="submit-btn"
            >
              {{ isSubmitting ? '提交中...' : '提交评论' }}
            </button>
          </div>
        </div>

        <!-- 评论列表 -->
        <div v-if="comments.length === 0" class="no-comments">
          <p>暂无评论，快来发表第一条评论吧！</p>
        </div>
        <div v-else class="comments-list">
          <div v-for="comment in comments" :key="comment.id" class="comment-card">
            <div class="comment-header">
              <span class="comment-author">{{ comment.username }}</span>
              <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
            </div>
            <div class="comment-content">{{ comment.content }}</div>
          </div>
        </div>

        <!-- 分页控制 -->
        <div class="pagination" v-if="comments.length > 0 && totalPages > 1">
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

// 获取讨论ID
const discussionId = computed(() => route.params.id);

// 讨论详情数据
const discussion = ref(null);
const relatedArticle = ref(null);
const loading = ref(true);
const error = ref(null);

// 评论数据
const comments = ref([]);
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value));

// 新评论
const newComment = ref({
  content: '',
  discussion_id: null
});
const isSubmitting = ref(false);

// 初始化加载
onMounted(async () => {
  if (!userStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  
  newComment.value.discussion_id = discussionId.value;
  
  try {
    // 获取讨论详情
    await fetchDiscussionDetail();
    
    // 获取评论列表
    await fetchComments();
  } catch (err) {
    error.value = '加载失败，请稍后再试';
    console.error('Error loading discussion:', err);
  } finally {
    loading.value = false;
  }
});

// 获取讨论详情
async function fetchDiscussionDetail() {
  try {
    const response = await axios.get(`http://localhost:8000/api/discussions/${discussionId.value}`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    discussion.value = response.data;
    
    // 如果讨论关联了法条，获取法条信息
    if (discussion.value.legal_article_id) {
      await fetchRelatedArticle(discussion.value.legal_article_id);
    }
  } catch (err) {
    console.error('Error fetching discussion:', err);
    throw err;
  }
}

// 获取关联的法条信息
async function fetchRelatedArticle(articleId) {
  try {
    const response = await axios.get(`http://localhost:8000/api/legal-articles/${articleId}`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    relatedArticle.value = response.data;
  } catch (err) {
    console.error('Error fetching related article:', err);
    // 不抛出错误，因为这不是关键信息
  }
}

// 获取评论列表
async function fetchComments() {
  try {
    const response = await axios.get(`http://localhost:8000/api/discussions/${discussionId.value}/comments`, {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value
      },
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    comments.value = response.data;
    
    // 获取总数量（实际项目中可能需要从响应头或专门的API获取）
    // 这里简化处理，假设返回的数据少于pageSize就是最后一页
    if (response.data.length < pageSize.value) {
      totalItems.value = (currentPage.value - 1) * pageSize.value + response.data.length;
    } else {
      // 如果返回的数据等于pageSize，则可能还有更多数据
      totalItems.value = currentPage.value * pageSize.value + 1;
    }
  } catch (err) {
    console.error('Error fetching comments:', err);
    throw err;
  }
}

// 提交评论
async function submitComment() {
  if (!newComment.value.content.trim()) {
    return;
  }
  
  isSubmitting.value = true;
  
  try {
    await axios.post(`http://localhost:8000/api/discussions/${discussionId.value}/comments`, 
      newComment.value, 
      {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      }
    );
    
    // 重置表单
    newComment.value.content = '';
    
    // 刷新评论列表
    await fetchComments();
  } catch (err) {
    console.error('Error submitting comment:', err);
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

.back-btn {
  display: flex;
  align-items: center;
  background-color: #f5f5f5;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
}

.back-icon {
  margin-right: 5px;
  font-size: 1.2em;
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

.loading, .error {
  text-align: center;
  padding: 50px;
  color: #666;
}

.error {
  color: #f44336;
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

.discussion-header h1 {
  margin: 0;
  color: #333;
  font-size: 1.8em;
}

.discussion-date {
  color: #666;
  font-size: 0.9em;
}

.discussion-author {
  color: #666;
  font-size: 0.9em;
  margin-bottom: 20px;
}

.discussion-content {
  margin-bottom: 30px;
  line-height: 1.6;
  color: #333;
  font-size: 1.1em;
}

.related-article {
  background-color: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.related-article h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #333;
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

.comments-section {
  margin-top: 30px;
}

.comments-section h2 {
  margin-bottom: 20px;
  color: #333;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
}

.new-comment-form {
  background-color: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 30px;
}

.new-comment-form h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #333;
}

.form-group {
  margin-bottom: 15px;
}

.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.submit-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.submit-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.no-comments {
  text-align: center;
  padding: 20px;
  color: #666;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.comment-card {
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

.page-info {
  color: #666;
}
</style>