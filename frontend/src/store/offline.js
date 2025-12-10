// Offline store for caching messages and sessions when network is unavailable
class OfflineStore {
  constructor() {
    this.storageKey = 'chatbot_offline_data'
    this.maxMessages = 100 // Maximum messages to store offline
    this.data = this.loadFromStorage()
  }
  
  loadFromStorage() {
    try {
      const stored = localStorage.getItem(this.storageKey)
      return stored ? JSON.parse(stored) : {
        messages: [],
        sessions: {},
        pendingRequests: []
      }
    } catch (error) {
      console.error('Error loading offline data:', error)
      return {
        messages: [],
        sessions: {},
        pendingRequests: []
      }
    }
  }
  
  saveToStorage() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.data))
    } catch (error) {
      console.error('Error saving offline data:', error)
    }
  }
  
  addMessage(sessionId, message) {
    const sessionMessages = this.data.sessions[sessionId] || []
    sessionMessages.push({
      ...message,
      timestamp: new Date().toISOString(),
      id: this.generateId()
    })
    
    // Keep only the latest messages
    if (sessionMessages.length > this.maxMessages) {
      sessionMessages.splice(0, sessionMessages.length - this.maxMessages)
    }
    
    this.data.sessions[sessionId] = sessionMessages
    this.saveToStorage()
  }
  
  getMessages(sessionId) {
    return this.data.sessions[sessionId] || []
  }
  
  getAllSessions() {
    return Object.keys(this.data.sessions)
  }
  
  clearMessages(sessionId) {
    if (sessionId) {
      delete this.data.sessions[sessionId]
    } else {
      this.data.sessions = {}
    }
    this.saveToStorage()
  }
  
  addPendingRequest(request) {
    this.data.pendingRequests.push({
      ...request,
      timestamp: new Date().toISOString(),
      id: this.generateId()
    })
    
    // Limit pending requests
    if (this.data.pendingRequests.length > 50) {
      this.data.pendingRequests.splice(0, this.data.pendingRequests.length - 50)
    }
    
    this.saveToStorage()
  }
  
  getPendingRequests() {
    return this.data.pendingRequests
  }
  
  clearPendingRequests() {
    this.data.pendingRequests = []
    this.saveToStorage()
  }
  
  markRequestAsCompleted(requestId) {
    this.data.pendingRequests = this.data.pendingRequests.filter(
      req => req.id !== requestId
    )
    this.saveToStorage()
  }
  
  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5)
  }
  
  // Sync with server when connection is restored
  async syncWithServer(apiService) {
    const pendingRequests = this.getPendingRequests()
    
    for (const request of pendingRequests) {
      try {
        // Attempt to send the request to the server
        await apiService.chatInference(request.data)
        
        // Mark as completed if successful
        this.markRequestAsCompleted(request.id)
        console.log(`Synced request ${request.id} with server`)
      } catch (error) {
        console.error(`Failed to sync request ${request.id}:`, error)
        // Keep the request for future sync attempts
      }
    }
  }
}

// Create a singleton instance
const offlineStore = new OfflineStore()

export default offlineStore