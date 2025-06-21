<template>
  <div class="profile-container" :class="{ 'senior-mode': seniorMode }">
    <div class="header">
      <h1>个人空间</h1>
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

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="profile-content">
      <!-- 个人信息卡片 -->
      <div class="profile-card">
        <div class="profile-header">
          <h2>个人信息</h2>
          <button v-if="!isEditing" @click="startEditing" class="edit-btn">
            编辑资料
          </button>
        </div>

        <!-- 查看模式 -->
        <div v-if="!isEditing" class="profile-details">
          <div class="detail-item">
            <span class="detail-label">用户名</span>
            <span class="detail-value">{{ userProfile.username }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">邮箱</span>
            <span class="detail-value">{{ userProfile.email }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">法律专业领域</span>
            <span class="detail-value">{{ userProfile.legal_specialty || '未设置' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">个人简介</span>
            <p class="detail-value bio">{{ userProfile.bio || '未设置个人简介' }}</p>
          </div>
          <div class="detail-item">
            <span class="detail-label">注册时间</span>
            <span class="detail-value">{{ formatDate(userProfile.created_at) }}</span>
          </div>
        </div>

        <!-- 编辑模式 -->
        <div v-else class="profile-edit-form">
          <div class="form-group">
            <label for="legal_specialty">法律专业领域</label>
            <input 
              id="legal_specialty" 
              v-model="editForm.legal_specialty" 
              type="text" 
              placeholder="请输入您的法律专业领域"
            />
          </div>
          <div class="form-group">
            <label for="bio">个人简介</label>
            <textarea 
              id="bio" 
              v-model="editForm.bio" 
              placeholder="请输入您的个人简介"
              rows="4"
            ></textarea>
          </div>
          <div class="form-actions">
            <button @click="cancelEditing" class="cancel-btn">取消</button>
            <button 
              @click="saveProfile" 
              :disabled="isSubmitting" 
              class="save-btn"
            >
              {{ isSubmitting ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 活动统计 -->
      <div class="stats-card">
        <h2>活动统计</h2>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ userStats.discussions_count }}</div>
            <div class="stat-label">发起的讨论</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ userStats.comments_count }}</div>
            <div class="stat-label">发表的评论</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ userStats.consultations_count }}</div>
            <div class="stat-label">法律咨询</div>
          </div>
        </div>
      </div>
      
      <!-- 活动图表 -->
      <div class="chart-card">
        <h2>近期活动趋势</h2>
        <div class="chart-tabs">
          <button 
            @click="activeChartType = 'line'" 
            :class="['chart-tab', { active: activeChartType === 'line' }]"
          >
            折线图
          </button>
          <button 
            @click="activeChartType = 'bar'" 
            :class="['chart-tab', { active: activeChartType === 'bar' }]"
          >
            柱状图
          </button>
        </div>
        <div ref="chartContainer" class="chart-container"></div>
      </div>

      <!-- 我的讨论 -->
      <div class="my-discussions">
        <div class="section-header">
          <h2>我的讨论</h2>
          <button @click="router.push('/discussions')" class="view-all-btn">
            查看全部
          </button>
        </div>

        <div v-if="myDiscussions.length === 0" class="no-data">
          <p>您还没有发起过讨论</p>
          <button @click="router.push('/discussions')" class="create-new-btn">
            去发起讨论
          </button>
        </div>
        <div v-else class="discussions-list">
          <div v-for="discussion in myDiscussions" :key="discussion.id" class="discussion-item">
            <div class="discussion-title">{{ discussion.title }}</div>
            <div class="discussion-meta">
              <span class="discussion-date">{{ formatDate(discussion.created_at) }}</span>
              <span class="discussion-comments">{{ discussion.comments_count }} 条评论</span>
            </div>
            <button @click="viewDiscussion(discussion.id)" class="view-btn">
              查看
            </button>
          </div>
        </div>
      </div>

      <!-- 最近的评论 -->
      <div class="my-comments">
        <div class="section-header">
          <h2>最近的评论</h2>
        </div>

        <div v-if="myComments.length === 0" class="no-data">
          <p>您还没有发表过评论</p>
        </div>
        <div v-else class="comments-list">
          <div v-for="comment in myComments" :key="comment.id" class="comment-item">
            <div class="comment-content">{{ comment.content }}</div>
            <div class="comment-meta">
              <span class="comment-date">{{ formatDate(comment.created_at) }}</span>
              <span class="comment-discussion">讨论: {{ comment.discussion_title }}</span>
            </div>
            <button @click="viewDiscussion(comment.discussion_id)" class="view-btn">
              查看讨论
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useUserStore } from '../stores/userStore';
import { useRouter } from 'vue-router';
import axios from 'axios';
import * as echarts from 'echarts';

const userStore = useUserStore();
const router = useRouter();

// 页面状态
const loading = ref(true);
const error = ref(null);

// 用户资料
const userProfile = ref({});
const userStats = ref({
  discussions_count: 0,
  comments_count: 0,
  consultations_count: 0
});

// 用户讨论和评论
const myDiscussions = ref([]);
const myComments = ref([]);

// 图表相关
const chartContainer = ref(null);
const myChart = ref(null);
const activeChartType = ref('line');
const userActivity = ref([]);

// 老年模式
const seniorMode = ref(false);

// 切换老年模式
function toggleSeniorMode() {
  seniorMode.value = !seniorMode.value;
}

// 编辑表单
const isEditing = ref(false);
const isSubmitting = ref(false);
const editForm = ref({
  legal_specialty: '',
  bio: ''
});

// 初始化加载
onMounted(async () => {
  if (!userStore.isAuthenticated) {
    router.push('/login');
    return;
  }
  
  try {
    // 获取用户资料
    await fetchUserProfile();
    
    // 获取用户统计数据
    await fetchUserStats();
    
    // 获取用户讨论
    await fetchUserDiscussions();
    
    // 获取用户评论
    await fetchUserComments();
    
    // 获取用户活动数据
    await fetchUserActivity();
    
    // 初始化图表
    initChart();
  } catch (err) {
    error.value = '加载失败，请稍后再试';
    console.error('Error loading user profile:', err);
  } finally {
    loading.value = false;
  }
});

// 导入模拟数据
import mockUserProfile from '../assets/mock-data/user-profile.json';
import mockUserStats from '../assets/mock-data/user-stats.json';
import mockDiscussions from '../assets/mock-data/discussions.json';
import mockUserComments from '../assets/mock-data/user-comments.json';
import mockUserActivity from '../assets/mock-data/user-activity.json';

// 获取用户资料
async function fetchUserProfile() {
  try {
    // 使用模拟数据
    userProfile.value = mockUserProfile;
    console.log('使用模拟用户资料数据：', userProfile.value);
  } catch (err) {
    console.error('Error fetching mock user profile:', err);
    throw err;
  }
}

// 获取用户统计数据
async function fetchUserStats() {
  try {
    // 使用模拟数据
    userStats.value = mockUserStats;
    console.log('使用模拟用户统计数据：', userStats.value);
  } catch (err) {
    console.error('Error fetching mock user stats:', err);
    // 不抛出错误，因为这不是关键信息
    userStats.value = {
      discussions_count: 0,
      comments_count: 0,
      consultations_count: 0
    };
  }
}

// 获取用户讨论
async function fetchUserDiscussions() {
  try {
    // 使用模拟数据，过滤出用户ID为1的讨论（假设当前用户ID为1）
    const userDiscussions = mockDiscussions.filter(discussion => discussion.user_id === 1);
    myDiscussions.value = userDiscussions.slice(0, 5); // 只取前5条
    console.log('使用模拟用户讨论数据：', myDiscussions.value);
  } catch (err) {
    console.error('Error fetching mock user discussions:', err);
    // 不抛出错误，因为这不是关键信息
  }
}

// 获取用户评论
async function fetchUserComments() {
  try {
    // 使用模拟数据
    myComments.value = mockUserComments;
    console.log('使用模拟用户评论数据：', myComments.value);
  } catch (err) {
    console.error('Error fetching mock user comments:', err);
    // 不抛出错误，因为这不是关键信息
  }
}

// 开始编辑资料
function startEditing() {
  editForm.value = {
    legal_specialty: userProfile.value.legal_specialty || '',
    bio: userProfile.value.bio || ''
  };
  isEditing.value = true;
}

// 取消编辑
function cancelEditing() {
  isEditing.value = false;
}

// 保存资料
async function saveProfile() {
  isSubmitting.value = true;
  
  try {
    // 使用模拟数据更新用户资料
    userProfile.value = {
      ...userProfile.value,
      legal_specialty: editForm.value.legal_specialty,
      bio: editForm.value.bio
    };
    
    // 退出编辑模式
    isEditing.value = false;
    
    // 显示成功消息
    alert('资料更新成功！');
    console.log('使用模拟数据更新用户资料：', userProfile.value);
  } catch (err) {
    console.error('Error updating user profile:', err);
    alert('更新资料失败，请稍后再试');
  } finally {
    isSubmitting.value = false;
  }
}

// 查看讨论详情
function viewDiscussion(discussionId) {
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

// 获取用户活动数据
async function fetchUserActivity() {
  try {
    // 使用模拟数据
    userActivity.value = mockUserActivity;
    console.log('使用模拟用户活动数据：', userActivity.value);
  } catch (err) {
    console.error('Error fetching mock user activity:', err);
    // 不抛出错误，因为这不是关键信息
  }
}

// 初始化图表
function initChart() {
  if (chartContainer.value) {
    myChart.value = echarts.init(chartContainer.value);
    updateChart();
    
    // 监听窗口大小变化，调整图表大小
    window.addEventListener('resize', () => {
      myChart.value?.resize();
    });
  }
}

// 更新图表
function updateChart() {
  if (!myChart.value || !userActivity.value.length) return;
  
  const dates = userActivity.value.map(item => item.date);
  const discussionsData = userActivity.value.map(item => item.discussions);
  const commentsData = userActivity.value.map(item => item.comments);
  const consultationsData = userActivity.value.map(item => item.consultations);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['讨论', '评论', '咨询']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        formatter: (value) => {
          const date = new Date(value);
          return `${date.getMonth() + 1}/${date.getDate()}`;
        }
      }
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '讨论',
        type: activeChartType.value,
        data: discussionsData,
        itemStyle: {
          color: '#2196F3'
        }
      },
      {
        name: '评论',
        type: activeChartType.value,
        data: commentsData,
        itemStyle: {
          color: '#4CAF50'
        }
      },
      {
        name: '咨询',
        type: activeChartType.value,
        data: consultationsData,
        itemStyle: {
          color: '#FF9800'
        }
      }
    ]
  };
  
  myChart.value.setOption(option);
}

// 监听图表类型变化
watch(activeChartType, () => {
  updateChart();
});
</script>

<style scoped>
.profile-container {
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

.loading, .error {
  text-align: center;
  padding: 50px;
  color: #666;
}

.error {
  color: #f44336;
}

.profile-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

@media (max-width: 768px) {
  .profile-content {
    grid-template-columns: 1fr;
  }
}

.profile-card, .stats-card, .my-discussions, .my-comments {
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.profile-card {
  grid-column: 1;
  grid-row: 1 / span 2;
}

.stats-card {
  grid-column: 2;
  grid-row: 1;
}

.my-discussions {
  grid-column: 2;
  grid-row: 2;
}

.my-comments {
  grid-column: 1 / span 2;
  grid-row: 3;
}

@media (max-width: 768px) {
  .profile-card, .stats-card, .my-discussions, .my-comments {
    grid-column: 1;
  }
  
  .profile-card {
    grid-row: 1;
  }
  
  .stats-card {
    grid-row: 2;
  }
  
  .my-discussions {
    grid-row: 3;
  }
  
  .my-comments {
    grid-row: 4;
  }
}

.profile-header, .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.profile-header h2, .section-header h2 {
  margin: 0;
  color: #333;
}

.edit-btn {
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.profile-details {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-label {
  font-weight: bold;
  color: #666;
  font-size: 0.9em;
}

.detail-value {
  color: #333;
}

.detail-value.bio {
  white-space: pre-line;
  line-height: 1.5;
}

.profile-edit-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-weight: bold;
  color: #666;
  font-size: 0.9em;
}

.form-group input, .form-group textarea {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1em;
}

.form-group textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.cancel-btn {
  background-color: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.save-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.save-btn:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.stat-value {
  font-size: 2em;
  font-weight: bold;
  color: #2196F3;
}

.stat-label {
  margin-top: 5px;
  color: #666;
  font-size: 0.9em;
}

.view-all-btn {
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.no-data {
  text-align: center;
  padding: 20px;
  color: #666;
  background-color: #f9f9f9;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.create-new-btn {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.discussions-list, .comments-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.discussion-item, .comment-item {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 15px;
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.discussion-title {
  font-weight: bold;
  color: #333;
  font-size: 1.1em;
}

.discussion-meta, .comment-meta {
  display: flex;
  justify-content: space-between;
  color: #666;
  font-size: 0.9em;
}

.comment-content {
  color: #333;
  line-height: 1.5;
}

.view-btn {
  align-self: flex-end;
  background-color: #2196F3;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}

/* 图表样式 */
.chart-card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 20px;
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 350px;
  margin-top: 15px;
}

.chart-tabs {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  margin-bottom: 15px;
}

.chart-tab {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #f5f5f5;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.chart-tab.active {
  background-color: #2196F3;
  color: white;
  border-color: #2196F3;
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

.senior-mode .profile-card,
.senior-mode .stats-card,
.senior-mode .my-discussions,
.senior-mode .my-comments,
.senior-mode .chart-card {
  border: 3px solid #2196f3;
  background: #fff;
  padding: 24px;
  border-radius: 15px;
  box-shadow: 0 8px 24px rgba(33, 150, 243, 0.1);
}

.senior-mode .stat-item {
  background: #e3f2fd;
  border: 2px solid #2196f3;
  padding: 20px;
  border-radius: 12px;
}

.senior-mode .stat-value {
  font-size: 250%;
  color: #2196f3;
}

.senior-mode .stat-label {
  font-size: 120%;
  font-weight: 600;
  color: #2196f3;
}

.senior-mode .discussion-item,
.senior-mode .comment-item {
  border: 3px solid #2196f3;
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(33, 150, 243, 0.1);
}

.senior-mode .discussion-title {
  font-size: 140%;
  font-weight: 700;
  color: #2196f3;
}

.senior-mode .comment-content {
  font-size: 130%;
  font-weight: 600;
  line-height: 1.8;
}

.senior-mode .detail-label {
  font-size: 120%;
  font-weight: 700;
  color: #2196f3;
}

.senior-mode .detail-value {
  font-size: 130%;
  font-weight: 600;
  color: #333;
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

.senior-mode .chart-tab {
  font-size: 120%;
  font-weight: 600;
  padding: 12px 20px;
  border: 3px solid #2196f3;
  background: #fff;
  color: #2196f3;
}

.senior-mode .chart-tab.active {
  background: #2196f3;
  color: white;
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