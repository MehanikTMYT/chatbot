<template>
  <div class="chat-view">
    <ChatInterface />
  </div>
</template>

<script>
import ChatInterface from '../components/ChatInterface.vue'

export default {
  name: 'ChatView',
  components: {
    ChatInterface
  }
}
</script>

<style scoped>
.chat-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  .chat-view {
    height: calc(100vh - 120px); /* Account for header and footer */
  }
}
</style>