import { createRouter, createWebHistory } from 'vue-router'
import ChatView from './views/ChatView.vue'
import DashboardView from './views/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'chat',
    component: ChatView
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router