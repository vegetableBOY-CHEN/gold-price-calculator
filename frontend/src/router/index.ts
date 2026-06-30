import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import CalculateView from '@/views/CalculateView.vue'
import RulesView from '@/views/RulesView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/calculate', name: 'calculate', component: CalculateView },
    { path: '/rules', name: 'rules', component: RulesView },
  ],
})

export default router
