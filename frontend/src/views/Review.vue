<script setup>
import { onMounted, reactive, ref } from 'vue'

import { api } from '../api/client'
import RiskBadge from '../components/RiskBadge.vue'

const deals = ref([])
const loading = ref(true)
const errorMessage = ref(null)
const partialAmounts = reactive({})
const busyDealId = ref(null)

async function load() {
  loading.value = true
  try {
    deals.value = await api.getReviewQueue()
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function resolve(deal, decision) {
  busyDealId.value = deal.id
  try {
    const payload = { decision }
    if (decision === 'partial') {
      payload.amount = parseFloat(partialAmounts[deal.id])
    }
    await api.resolveReview(deal.id, payload)
    await load()
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    busyDealId.value = null
  }
}
</script>

<template>
  <h1>Human review queue</h1>
  <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
  <p v-if="loading" class="muted">Loading…</p>
  <p v-else-if="!deals.length" class="muted">Nothing needs review right now.</p>

  <div v-for="deal in deals" :key="deal.id" class="card review-card">
    <div class="review-head">
      <h2>{{ deal.title }}</h2>
      <span class="price">${{ deal.price.toFixed(2) }}</span>
    </div>

    <RiskBadge :risk-score="deal.risk_score" :risk-reasons="deal.risk_reasons" />

    <div class="photo-compare">
      <div>
        <p class="muted">Listing photo</p>
        <img v-if="deal.photo_urls[0]" :src="deal.photo_urls[0]" alt="Listing photo" />
        <p v-else class="muted">No listing photo provided</p>
      </div>
      <div>
        <p class="muted">Buyer's received photo</p>
        <img v-if="deal.buyer_photo_url" :src="deal.buyer_photo_url" alt="Buyer photo" />
        <p v-else class="muted">No photo uploaded</p>
      </div>
    </div>

    <div class="decision-row">
      <button class="btn btn-primary" :disabled="busyDealId === deal.id" @click="resolve(deal, 'capture')">
        Capture full amount
      </button>
      <div class="partial">
        <input
          v-model="partialAmounts[deal.id]"
          type="number"
          min="0"
          :max="deal.price"
          step="0.01"
          placeholder="Partial amount"
        />
        <button
          class="btn btn-secondary"
          :disabled="busyDealId === deal.id || !partialAmounts[deal.id]"
          @click="resolve(deal, 'partial')"
        >
          Partial capture
        </button>
      </div>
      <button class="btn btn-danger" :disabled="busyDealId === deal.id" @click="resolve(deal, 'void')">
        Void
      </button>
    </div>

    <RouterLink class="muted timeline-link" :to="`/deal/${deal.id}/timeline`">
      View full timeline
    </RouterLink>
  </div>
</template>

<style scoped>
h1 {
  font-size: 1.5rem;
}

.review-card + .review-card {
  margin-top: 1.25rem;
}

.review-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.review-head h2 {
  font-size: 1.15rem;
  margin: 0;
}

.price {
  font-weight: 700;
  color: var(--accent);
}

.photo-compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin: 1rem 0;
}

.photo-compare img {
  width: 100%;
  border-radius: 8px;
  border: 1px solid var(--border);
}

.decision-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1rem;
}

.partial {
  display: flex;
  gap: 0.5rem;
}

.partial input {
  width: 130px;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 8px;
}

.timeline-link {
  display: inline-block;
  margin-top: 0.75rem;
  font-size: 0.85rem;
  text-decoration: underline;
}
</style>
