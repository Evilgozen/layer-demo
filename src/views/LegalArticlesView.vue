<template>
  <div class="legal-articles-container">
    <div class="header">
      <h1>法条查询</h1>
      <div class="user-info" v-if="userStore.user">
        <span>欢迎, {{ userStore.user.username }}</span>
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </div>

    <div class="search-panel">
      <div class="search-form">
        <div class="search-row">
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="输入关键词搜索法条..."
            @keyup.enter="searchArticles"
          />
          <select v-model="searchCategory">
            <option value="">全部分类</option>
            <option value="民法">民法</option>
            <option value="刑法">刑法</option>
            <option value="行政法">行政法</option>
            <option value="劳动法">劳动法</option>
            <option value="婚姻法">婚姻法</option>
            <option value="合同法">合同法</option>
            <option value="其他">其他</option>
          </select>
          <select v-model="searchSource">
            <option value="">全部来源</option>
            <option value="中华人民共和国民法典">中华人民共和国民法典</option>
            <option value="中华人民共和国刑法">中华人民共和国刑法</option>
            <option value="中华人民共和国劳动法">中华人民共和国劳动法</option>
            <option value="中华人民共和国婚姻法">中华人民共和国婚姻法</option>
            <option value="中华人民共和国合同法">中华人民共和国合同法</option>
          </select>
          <button @click="searchArticles" class="search-btn">搜索</button>
        </div>
      </div>
    </div>

    <div class="articles-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="articles.length === 0" class="no-results">
        <p>没有找到符合条件的法条</p>
      </div>
      <div v-else class="article-cards">
        <div v-for="article in articles" :key="article.id" class="article-card">
          <div class="article-header">
            <h3>{{ article.title }}</h3>
            <span class="article-number">{{ article.article_number }}</span>
          </div>
          <div class="article-source">{{ article.source }}</div>
          <div class="article-content">{{ article.content }}</div>
          <div class="article-footer">
            <span class="article-category">{{ article.category }}</span>
            <div class="article-actions">
              <button @click="viewArticleDetail(article.id)" class="view-detail-btn">
                查看详情
              </button>
              <button @click="viewDiscussions(article.id)" class="view-discussions-btn">
                查看讨论
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="pagination" v-if="articles.length > 0">
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
import { useRouter } from 'vue-router';
import axios from 'axios';

const userStore = useUserStore();
const router = useRouter();

// 搜索参数
const searchKeyword = ref('');
const searchCategory = ref('');
const searchSource = ref('');

// 分页参数
const currentPage = ref(1);
const pageSize = ref(10);
const totalItems = ref(0);
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value));

// 法条数据
const articles = ref([]);
const loading = ref(false);

// 初始化加载
onMounted(async () => {
  if (!userStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  
  await searchArticles();
});

// 导入模拟数据
import mockLegalArticles from '../assets/mock-data/legal-articles.json';

// 搜索法条
async function searchArticles() {
  loading.value = true;
  
  try {
    // 使用模拟数据而不是API请求
    let filteredArticles = [...mockLegalArticles];
    
    // 应用过滤条件
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase();
      filteredArticles = filteredArticles.filter(article => 
        article.title.toLowerCase().includes(keyword) || 
        article.content.toLowerCase().includes(keyword) || 
        article.article_number.toLowerCase().includes(keyword)
      );
    }
    
    if (searchCategory.value) {
      filteredArticles = filteredArticles.filter(article => 
        article.category === searchCategory.value
      );
    }
    
    if (searchSource.value) {
      filteredArticles = filteredArticles.filter(article => 
        article.source === searchSource.value
      );
    }
    
    // 计算总数量
    totalItems.value = filteredArticles.length;
    
    // 分页处理
    const start = (currentPage.value - 1) * pageSize.value;
    const end = start + pageSize.value;
    articles.value = filteredArticles.slice(start, end);
    
    console.log('使用模拟数据：', articles.value);
  } catch (error) {
    console.error('Error processing mock legal articles:', error);
    // 处理错误，例如显示错误消息
  } finally {
    loading.value = false;
  }
}

// 分页控制
function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--;
    searchArticles();
  }
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++;
    searchArticles();
  }
}

// 查看法律条文详情
function viewArticleDetail(articleId) {
  router.push(`/legal-article/${articleId}`);
}

// 查看讨论
function viewDiscussions(articleId) {
  router.push(`/discussions?articleId=${articleId}`);
}

// 退出登录
function logout() {
  userStore.logout();
  router.push('/login');
}
</script>

<style scoped>
.legal-articles-container {
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

.search-panel {
  background-color: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

input, select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  flex: 1;
}

.search-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
}

.articles-list {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.loading, .no-results {
  text-align: center;
  padding: 20px;
  color: #666;
}

.article-cards {
  display: flex;
  flex-direction: column;
  gap: 20px;
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

.article-actions {
  display: flex;
  gap: 10px;
}

.article-category {
  background-color: #e0e0e0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8em;
}

.view-detail-btn {
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8em;
}

.view-detail-btn:hover {
  background-color: #0b7dda;
}

.view-discussions-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8em;
}

.view-discussions-btn:hover {
  background-color: #45a049;
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