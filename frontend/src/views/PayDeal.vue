<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import PayPalButton from '../components/PayPalButton.vue'
import RiskBadge from '../components/RiskBadge.vue'
import { useDealStore } from '../stores/deal'

const props = defineProps({
  id: { type: String, required: true },
})

const store = useDealStore()
const router = useRouter()

onMounted(() => {
  store.fetchDeal(props.id)
})

function onAuthorized() {
  router.push(`/deal/${props.id}/timeline`)
}
</script>

<template>
  <div v-if="store.loading" class="muted">Loading deal…</div>
  <p v-else-if="store.error" class="error-text">{{ store.error }}</p>

  <div v-else-if="store.deal" class="card">
    <h1>{{ store.deal.title }}</h1>
    <p class="price">${{ store.deal.price.toFixed(2) }}</p>
    <p v-if="store.deal.description">{{ store.deal.description }}</p>

    <RiskBadge :risk-score="store.deal.risk_score" :risk-reasons="store.deal.risk_reasons" />

    <div class="how-strip">
      <span>Pay with hold</span>
      <span>&rarr;</span>
      <span>AI verifies delivery</span>
      <span>&rarr;</span>
      <span>Release or void</span>
    </div>

    <div v-if="store.deal.status === 'SCREENED'" class="pay-section">
      <PayPalButton :deal-id="id" @authorized="onAuthorized" />
    </div>
    <div v-else class="already-moving">
      <p class="muted">
        This deal is already in progress (status: <strong>{{ store.deal.status }}</strong>).
      </p>
      <RouterLink class="btn btn-secondary" :to="`/deal/${id}/timeline`">View timeline</RouterLink>
    </div>
  </div>
</template>

<style scoped>
h1 {
  font-size: 1.5rem;
  margin: 0 0 0.25rem;
}

.price {
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--accent);
  margin: 0 0 1rem;
}

.how-strip {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 1.25rem 0;
  padding: 0.75rem 1rem;
  background: var(--bg);
  border-radius: 8px;
  font-size: 0.85rem;
  color: var(--text-muted);
  flex-wrap: wrap;
}

.pay-section {
  margin-top: 1.5rem;
}

.already-moving {
  margin-top: 1.5rem;
}
</style>
