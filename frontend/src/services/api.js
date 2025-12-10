import axios from 'axios'
import networkManager from '../plugins/network'

class ApiService {
  constructor() {
    this.baseURL = this.getBaseURL()
    this.apiClient = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      }
    })
    
    this.setupInterceptors()
  }
  
  getBaseURL() {
    // Determine the base URL based on network mode
    const networkMode = networkManager.getConnectionMode()
    
    switch(networkMode) {
      case 'direct':
        // Try to connect directly to local inference server
        return `http://${window.location.hostname}:8001` // Local inference server
      case 'relay':
        // Connect through VDS
        return '' // Use relative path to go through VDS
      case 'offline':
        // In offline mode, we might use cached responses or local storage
        return null
      default:
        return '' // Default to relative path
    }
  }
  
  setupInterceptors() {
    // Request interceptor to handle network changes
    this.apiClient.interceptors.request.use(
      (config) => {
        // Update base URL if network mode changed
        const currentNetworkMode = networkManager.getConnectionMode()
        if (this.lastNetworkMode !== currentNetworkMode) {
          this.baseURL = this.getBaseURL()
          config.baseURL = this.baseURL
          this.lastNetworkMode = currentNetworkMode
        }
        
        // Add auth token if available
        const token = localStorage.getItem('authToken')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )
    
    // Response interceptor to handle network errors and fallbacks
    this.apiClient.interceptors.response.use(
      (response) => {
        return response
      },
      (error) => {
        console.error('API Error:', error)
        
        // Handle network errors
        if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
          console.log('Request timed out, attempting reconnect...')
          networkManager.attemptReconnect()
        } else if (error.response?.status >= 500) {
          console.log('Server error, checking network status...')
          networkManager.detectNetworkMode()
        }
        
        return Promise.reject(error)
      }
    )
  }
  
  // Method to update the API client configuration when network mode changes
  updateNetworkConfig() {
    const newBaseURL = this.getBaseURL()
    if (newBaseURL !== this.baseURL) {
      this.baseURL = newBaseURL
      this.apiClient.defaults.baseURL = this.baseURL
    }
  }
  
  // API methods
  async healthCheck() {
    try {
      const response = await this.apiClient.get('/health')
      return response.data
    } catch (error) {
      console.error('Health check failed:', error)
      throw error
    }
  }
  
  async chatInference(data) {
    try {
      const response = await this.apiClient.post('/infer', data)
      return response.data
    } catch (error) {
      console.error('Chat inference failed:', error)
      throw error
    }
  }
  
  async login(credentials) {
    try {
      const response = await this.apiClient.post('/auth/login', credentials)
      return response.data
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }
  
  async register(userData) {
    try {
      const response = await this.apiClient.post('/auth/register', userData)
      return response.data
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }
}

// Create a singleton instance
const apiService = new ApiService()

// Listen for network changes and update API configuration
networkManager.setupEventListeners = function() {
  // Override to add API service update
  const originalSetup = this.constructor.prototype.setupEventListeners
  if (originalSetup) {
    originalSetup.call(this)
  }
  
  // Add our own network change handler
  window.addEventListener('online', () => {
    setTimeout(() => apiService.updateNetworkConfig(), 1000)
  })
  
  window.addEventListener('offline', () => {
    // In offline mode, we might want to queue requests
    console.log('Switched to offline mode, API requests will be queued')
  })
}

export default apiService