import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import LoginView from '../views/LoginView.vue'
import AiAssistantView from '../views/AiAssistantView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: AiAssistantView,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { guest: true }
    }
  ],
})

// Navigation Guards
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const isGuest = to.matched.some(record => record.meta.guest)
  
  // Check if user is authenticated
  if (requiresAuth && !userStore.isAuthenticated) {
    // Redirect to login page if not authenticated
    next('/login')
  } else if (isGuest && userStore.isAuthenticated && to.path === '/login') {
    // Only redirect from login page if already authenticated
    // This allows access to register page even when authenticated
    next('/')
  } else {
    // Proceed as normal
    next()
  }
})

export default router
