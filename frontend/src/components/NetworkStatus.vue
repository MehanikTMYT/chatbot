<template>
  <div class="network-status" :class="statusClass">
    <span class="status-icon" :class="iconClass"></span>
    <span class="status-text">{{ statusText }}</span>
    <span class="connection-mode">({{ networkMode }})</span>
  </div>
</template>

<script>
import networkManager from '../plugins/network'

export default {
  name: 'NetworkStatus',
  data() {
    return {
      networkStatus: networkManager.getNetworkStatus()
    }
  },
  computed: {
    statusText() {
      if (this.networkStatus.isOnline) {
        switch (this.networkStatus.connectionMode) {
          case 'direct':
            return 'Direct (LAN)'
          case 'relay':
            return 'Relay (VDS)'
          case 'hybrid':
            return 'Hybrid'
          default:
            return 'Connected'
        }
      } else {
        return 'Offline'
      }
    },
    networkMode() {
      return this.networkStatus.connectionMode
    },
    statusClass() {
      if (!this.networkStatus.isOnline) {
        return 'offline'
      }
      switch (this.networkStatus.connectionMode) {
        case 'direct':
          return 'direct'
        case 'relay':
          return 'relay'
        case 'hybrid':
          return 'hybrid'
        default:
          return 'connected'
      }
    },
    iconClass() {
      if (!this.networkStatus.isOnline) {
        return 'offline-icon'
      }
      switch (this.networkStatus.connectionMode) {
        case 'direct':
          return 'direct-icon'
        case 'relay':
          return 'relay-icon'
        case 'hybrid':
          return 'hybrid-icon'
        default:
          return 'connected-icon'
      }
    }
  },
  mounted() {
    // Update network status periodically
    setInterval(() => {
      this.networkStatus = networkManager.getNetworkStatus()
    }, 3000) // Update every 3 seconds
  }
}
</script>

<style scoped>
.network-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-icon {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
}

.direct {
  background-color: rgba(46, 204, 113, 0.1);
  border: 1px solid rgba(46, 204, 113, 0.3);
  color: #2ecc71;
}

.direct-icon {
  background-color: #2ecc71;
}

.relay {
  background-color: rgba(52, 152, 219, 0.1);
  border: 1px solid rgba(52, 152, 219, 0.3);
  color: #3498db;
}

.relay-icon {
  background-color: #3498db;
}

.hybrid {
  background-color: rgba(155, 89, 182, 0.1);
  border: 1px solid rgba(155, 89, 182, 0.3);
  color: #9b59b6;
}

.hybrid-icon {
  background-color: #9b59b6;
}

.offline {
  background-color: rgba(231, 76, 60, 0.1);
  border: 1px solid rgba(231, 76, 60, 0.3);
  color: #e74c3c;
}

.offline-icon {
  background-color: #e74c3c;
}

.status-text {
  font-weight: 600;
}

.connection-mode {
  font-size: 0.75rem;
  opacity: 0.8;
}
</style>