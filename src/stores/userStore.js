import { defineStore } from 'pinia'
import axios from 'axios'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null,
    loading: false,
    error: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    getUser: (state) => state.user,
    getError: (state) => state.error,
    isLoading: (state) => state.loading
  },
  
  actions: {
    async register(userData) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.post('http://localhost:8000/register', userData)
        this.loading = false
        return response.data
      } catch (error) {
        this.loading = false
        this.error = error.response?.data?.detail || 'Registration failed'
        throw error
      }
    },
    
    async login(username, password) {
      this.loading = true
      this.error = null
      
      try {
        // 确保设置正确的Content-Type头部
        const response = await axios.post('http://127.0.0.1:8000/login', {
          username,
          password
        }, {
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        this.token = response.data.access_token
        localStorage.setItem('token', this.token)
        
        // Fetch user data
        await this.fetchUserData()
        
        this.loading = false
        return { success: true, data: response.data }
      } catch (error) {
        this.loading = false
        this.error = error.response?.data?.detail || 'Login failed'
        console.error('Login error details:', error.response?.data)
        return false
      }
    },
    
    async fetchUserData() {
      if (!this.token) return null
      
      this.loading = true
      
      try {
        const response = await axios.get('http://localhost:8000/users/me', {
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        })
        
        this.user = response.data
        this.loading = false
        return this.user
      } catch (error) {
        this.loading = false
        if (error.response?.status === 401) {
          this.logout()
        }
        this.error = error.response?.data?.detail || 'Failed to fetch user data'
        return null
      }
    },
    
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
    }
  }
})
