<template>
  <div class="chat-container">
    <div class="messages-container" ref="messagesContainer">
      <div 
        v-for="message in messages" 
        :key="message.id" 
        :class="['message', message.sender]"
      >
        <div class="message-content">
          <div class="message-text">{{ message.text }}</div>
          <div class="message-info">
            <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
            <span class="engine-info" v-if="message.engine">via {{ message.engine }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="input-container">
      <textarea
        v-model="inputMessage"
        @keydown.enter.exact="sendMessage"
        @keydown.enter.shift.exact="addNewLine"
        placeholder="Type your message..."
        rows="1"
        :disabled="isProcessing"
      ></textarea>
      <button 
        @click="sendMessage" 
        :disabled="isProcessing || !inputMessage.trim()"
        class="send-button"
      >
        {{ isProcessing ? 'Sending...' : 'Send' }}
      </button>
    </div>
  </div>
</template>

<script>
import apiService from '../services/api'
import offlineStore from '../store/offline'
import networkManager from '../plugins/network'

export default {
  name: 'ChatInterface',
  data() {
    return {
      messages: [],
      inputMessage: '',
      isProcessing: false,
      sessionId: this.generateSessionId(),
      networkMode: networkManager.getConnectionMode()
    }
  },
  mounted() {
    // Load messages from offline store if available
    this.messages = offlineStore.getMessages(this.sessionId)
    
    // Listen for network changes
    setInterval(() => {
      const newNetworkMode = networkManager.getConnectionMode()
      if (newNetworkMode !== this.networkMode) {
        this.networkMode = newNetworkMode
        this.handleNetworkChange()
      }
    }, 3000)
    
    // Scroll to bottom when messages change
    this.$nextTick(() => {
      this.scrollToBottom()
    })
  },
  watch: {
    messages: {
      handler() {
        this.$nextTick(() => {
          this.scrollToBottom()
        })
      },
      deep: true
    }
  },
  methods: {
    async sendMessage() {
      if (!this.inputMessage.trim() || this.isProcessing) {
        return
      }
      
      const userMessage = {
        text: this.inputMessage.trim(),
        sender: 'user',
        timestamp: new Date().toISOString(),
        id: this.generateId()
      }
      
      // Add user message to UI immediately
      this.messages.push(userMessage)
      const userInput = this.inputMessage
      this.inputMessage = ''
      this.adjustTextareaHeight()
      
      this.isProcessing = true
      
      try {
        // Check network status
        const networkStatus = networkManager.getNetworkStatus()
        
        if (!networkStatus.isOnline) {
          // Handle offline mode
          const offlineResponse = {
            text: "I'm currently in offline mode. Your message has been saved and will be processed when connection is restored.",
            sender: 'bot',
            timestamp: new Date().toISOString(),
            id: this.generateId(),
            engine: 'offline-cache'
          }
          this.messages.push(offlineResponse)
          
          // Save to offline store for later processing
          offlineStore.addPendingRequest({
            data: { text: userInput, sessionId: this.sessionId }
          })
        } else {
          // Send to API service
          const response = await apiService.chatInference({
            text: userInput,
            sessionId: this.sessionId
          })
          
          const botMessage = {
            text: response.result?.content || response.result || 'Sorry, I could not process your request.',
            sender: 'bot',
            timestamp: new Date().toISOString(),
            id: this.generateId(),
            engine: response.engine || 'unknown'
          }
          
          this.messages.push(botMessage)
        }
      } catch (error) {
        console.error('Error sending message:', error)
        
        // Add error message
        const errorMessage = {
          text: "Sorry, there was an error processing your message. Please try again.",
          sender: 'bot',
          timestamp: new Date().toISOString(),
          id: this.generateId(),
          engine: 'error'
        }
        this.messages.push(errorMessage)
      } finally {
        this.isProcessing = false
      }
      
      // Save messages to offline store
      this.saveMessagesToOfflineStore()
    },
    
    addNewLine(event) {
      // Add a new line when Shift+Enter is pressed
      this.inputMessage += '\n'
      event.preventDefault()
    },
    
    adjustTextareaHeight() {
      this.$nextTick(() => {
        const textarea = this.$el.querySelector('textarea')
        if (textarea) {
          textarea.style.height = 'auto'
          textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
        }
      })
    },
    
    scrollToBottom() {
      const container = this.$refs.messagesContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    },
    
    formatTime(timestamp) {
      const date = new Date(timestamp)
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },
    
    generateId() {
      return Date.now().toString(36) + Math.random().toString(36).substr(2, 5)
    },
    
    generateSessionId() {
      // Create a session ID based on current time and random value
      return `session_${Date.now().toString(36)}_${Math.random().toString(36).substr(2, 5)}`
    },
    
    handleNetworkChange() {
      const networkStatus = networkManager.getNetworkStatus()
      
      if (networkStatus.isOnline && this.networkMode !== 'offline') {
        // Try to sync with server
        this.syncWithServer()
      }
    },
    
    async syncWithServer() {
      try {
        await offlineStore.syncWithServer(apiService)
        // Reload messages after sync
        this.messages = offlineStore.getMessages(this.sessionId)
      } catch (error) {
        console.error('Error syncing with server:', error)
      }
    },
    
    saveMessagesToOfflineStore() {
      // Save all messages to offline store
      this.messages.forEach(message => {
        offlineStore.addMessage(this.sessionId, message)
      })
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background-color: #f9f9f9;
}

.message {
  display: flex;
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
}

.message.bot {
  align-self: flex-start;
}

.message-content {
  padding: 0.75rem 1rem;
  border-radius: 18px;
  position: relative;
}

.message.user .message-content {
  background-color: #3498db;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.bot .message-content {
  background-color: #ecf0f1;
  color: #2c3e50;
  border-bottom-left-radius: 4px;
}

.message-text {
  margin-bottom: 0.25rem;
  line-height: 1.4;
  white-space: pre-wrap;
}

.message-info {
  font-size: 0.75rem;
  opacity: 0.7;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.timestamp {
  font-style: italic;
}

.engine-info {
  text-transform: uppercase;
}

.input-container {
  display: flex;
  padding: 1rem;
  background: white;
  border-top: 1px solid #eee;
  gap: 0.5rem;
}

.input-container textarea {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 18px;
  padding: 0.75rem 1rem;
  resize: none;
  font-family: inherit;
  font-size: 1rem;
  min-height: 40px;
  max-height: 150px;
  outline: none;
  transition: border-color 0.2s;
}

.input-container textarea:focus {
  border-color: #3498db;
}

.send-button {
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 18px;
  padding: 0 1.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.send-button:hover:not(:disabled) {
  background-color: #2980b9;
}

.send-button:disabled {
  background-color: #bdc3c7;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .chat-container {
    margin: 0;
    border-radius: 0;
    height: 100vh;
  }
  
  .message {
    max-width: 90%;
  }
}
</style>