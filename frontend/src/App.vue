<template>
  <div id="app">
    <header class="app-header">
      <h1>Hybrid Chatbot</h1>
      <NetworkStatus />
    </header>
    <main class="app-main">
      <router-view />
    </main>
    <footer class="app-footer">
      <p>Secure Local Chatbot System | {{ networkStatus.connectionMode }} mode</p>
    </footer>
  </div>
</template>

<script>
import NetworkStatus from './components/NetworkStatus.vue'
import networkManager from './plugins/network'

export default {
  name: 'App',
  components: {
    NetworkStatus
  },
  data() {
    return {
      networkStatus: networkManager.getNetworkStatus()
    }
  },
  mounted() {
    // Update network status periodically
    setInterval(() => {
      this.networkStatus = networkManager.getNetworkStatus()
    }, 5000) // Update every 5 seconds
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: #34495e;
  color: white;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-header h1 {
  margin: 0;
  font-size: 1.5rem;
}

.app-main {
  flex: 1;
  padding: 1rem;
}

.app-footer {
  background-color: #ecf0f1;
  padding: 0.5rem;
  border-top: 1px solid #bdc3c7;
}

@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .app-header h1 {
    font-size: 1.2rem;
  }
}
</style>