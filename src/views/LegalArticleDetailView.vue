<template>
  <div class="legal-article-detail-container">
    <div class="header">
      <h1>法条详情</h1>
      <div class="user-info" v-if="userStore.user">
        <span>欢迎, {{ userStore.user.username }}</span>
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </div>

    <div class="article-content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="article" class="article-card">
        <div class="article-header">
          <h2>{{ article.title }}</h2>
          <span class="article-number">{{ article.article_number }}</span>
        </div>
        <div class="article-source">{{ article.source }}</div>
        <div class="article-content-text">{{ article.content }}</div>
        <div class="article-footer">
          <span class="article-category">{{ article.category }}</span>
          <button @click="viewDiscussions(article.id)" class="view-discussions-btn">
            查看相关讨论
          </button>
        </div>
      </div>
      <div v-else class="no-article">
        <p>未找到法条信息</p>
      </div>

      <div class="actions">
        <button @click="goBack" class="back-btn">返回列表</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '../stores/userStore';

// 导入模拟数据
import mockLegalArticles from '../assets/mock-data/legal-articles.json';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const article = ref(null);
const loading = ref(true);
const error = ref(null);

const articleId = computed(() => route.params.id);

onMounted(async () => {
  // 检查用户是否已登录
  if (!userStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  
  try {
    await fetchArticle();
  } catch (err) {
    error.value = '获取法律条文失败，请稍后再试';
  } finally {
    loading.value = false;
  }
});

async function fetchArticle() {
  try {
    // 使用模拟数据获取法律条文
    const foundArticle = mockLegalArticles.find(a => a.id === parseInt(articleId.value));
    if (foundArticle) {
      article.value = foundArticle;
      console.log('使用模拟数据获取法律条文：', article.value);
    } else {
      throw new Error('未找到对应的法律条文');
    }
  } catch (err) {
    console.error('Error fetching article:', err);
    throw err;
  }
}

// 查看讨论
function viewDiscussions(articleId) {
  router.push(`/discussions?articleId=${articleId}`);
}

// 返回列表
function goBack() {
  router.push('/legal-articles');
}

// 退出登录
function logout() {
  userStore.logout();
  router.push('/login');
}
</script>

<style scoped>
.legal-article-detail-container {
  max-width: 1000px;
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
}

.user-info span {
  margin-right: 10px;
}

.logout-btn {
  background-color: #f44336;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
}

.article-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.article-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.article-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5em;
}

.article-number {
  color: #666;
  font-size: 1em;
  font-weight: bold;
}

.article-source {
  color: #666;
  font-size: 0.9em;
  margin-bottom: 15px;
}

.article-content-text {
  color: #333;
  line-height: 1.6;
  margin-bottom: 20px;
  font-size: 1.1em;
  white-space: pre-line;
}

.article-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
}

.article-category {
  background-color: #e0e0e0;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.8em;
}

.view-discussions-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}

.view-discussions-btn:hover {
  background-color: #45a049;
}

.actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.back-btn {
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
}

.back-btn:hover {
  background-color: #0b7dda;
}

.loading, .error, .no-article {
  text-align: center;
  padding: 50px;
  color: #666;
}

.error {
  color: #f44336;
}
</style>