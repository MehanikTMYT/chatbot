// Network detection plugin for the hybrid chatbot
class NetworkManager {
  constructor() {
    this.connectionMode = 'relay' // default mode
    this.isOnline = navigator.onLine
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 10
    this.reconnectDelay = 5000 // 5 seconds
    
    this.setupEventListeners()
    this.detectNetworkMode()
  }
  
  setupEventListeners() {
    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.isOnline = true
      this.onNetworkChange()
    })
    
    window.addEventListener('offline', () => {
      this.isOnline = false
      this.onNetworkChange()
    })
  }
  
  async detectNetworkMode() {
    // Try to detect if we're on the same network as the local inference server
    try {
      // First, try to reach the local inference server
      const localResponse = await fetch(`http://${window.location.hostname}:8001/health`, {
        method: 'GET',
        mode: 'no-cors' // This might not work due to CORS, but we'll try
      })
      
      if (localResponse.ok) {
        this.connectionMode = 'direct'
      } else {
        // If local server is not accessible, check if we can reach the VDS
        const vdsResponse = await fetch('/health')
        if (vdsResponse.ok) {
          this.connectionMode = 'relay'
        } else {
          this.connectionMode = 'offline'
        }
      }
    } catch (error) {
      // If all network requests fail, we're in offline mode
      this.connectionMode = 'offline'
    }
    
    console.log(`Network mode detected: ${this.connectionMode}`)
    return this.connectionMode
  }
  
  onNetworkChange() {
    console.log(`Network status changed: ${this.isOnline ? 'online' : 'offline'}`)
    this.detectNetworkMode()
  }
  
  getConnectionMode() {
    return this.connectionMode
  }
  
  getNetworkStatus() {
    return {
      isOnline: this.isOnline,
      connectionMode: this.connectionMode,
      timestamp: new Date().toISOString()
    }
  }
  
  async attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      setTimeout(() => {
        this.detectNetworkMode()
      }, this.reconnectDelay)
    } else {
      console.log('Max reconnect attempts reached')
    }
  }
}

// Create a singleton instance
const networkManager = new NetworkManager()

export default networkManager