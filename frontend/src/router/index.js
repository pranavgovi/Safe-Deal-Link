import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'landing', component: () => import('../views/Landing.vue') },
  { path: '/new', name: 'create-deal', component: () => import('../views/CreateDeal.vue') },
  { path: '/deal/:id', name: 'pay-deal', component: () => import('../views/PayDeal.vue'), props: true },
  {
    path: '/deal/:id/timeline',
    name: 'deal-timeline',
    component: () => import('../views/DealTimeline.vue'),
    props: true,
  },
  { path: '/review', name: 'review', component: () => import('../views/Review.vue') },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
