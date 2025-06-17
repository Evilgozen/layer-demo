<template>
  <div class="profile-container">
    <div class="header">
      <h1>个人空间</h1>
      <div class="user-info" v-if="userStore.user">
        <span>欢迎, {{ userStore.user.username }}</span>
        <button @click="logout" class="logout-btn">退出登录</button>
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
import { ref, onMounted } from 'vue';
import { useUserStore } from '../stores/userStore';
import { useRouter } from 'vue-router';
import axios from 'axios';

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
</style>