<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { api } from '../api/client'
import AgentTimeline from '../components/AgentTimeline.vue'
import RiskBadge from '../components/RiskBadge.vue'
import { useDealStore } from '../stores/deal'

const props = defineProps({
  id: { type: String, required: true },
})

const store = useDealStore()

const carrier = ref('')
const trackingNumber = ref('')
const shipSubmitting = ref(false)
const shipError = ref(null)

const deliveredSubmitting = ref(false)

const photoFile = ref(null)
const photoSubmitting = ref(false)
const photoError = ref(null)

onMounted(() => {
  store.refresh(props.id)
  store.startPolling(props.id)
})

onUnmounted(() => {
  store.stopPolling()
})

const statusTone = computed(() => {
  const status = store.status
  if (status === 'CAPTURED') return 'success'
  if (status === 'VOIDED') return 'danger'
  if (status === 'NEEDS_HUMAN') return 'warning'
  return 'neutral'
})

async function submitTracking() {
  shipError.value = null
  shipSubmitting.value = true
  try {
    await api.addTracking(props.id, { carrier: carrier.value, tracking_number: trackingNumber.value })
    await store.refresh(props.id)
  } catch (err) {
    shipError.value = err.message
  } finally {
    shipSubmitting.value = false
  }
}

async function markDelivered() {
  deliveredSubmitting.value = true
  try {
    await api.markDelivered(props.id)
    await store.refresh(props.id)
  } finally {
    deliveredSubmitting.value = false
  }
}

function onFileChange(event) {
  photoFile.value = event.target.files[0] || null
}

async function submitPhoto() {
  if (!photoFile.value) return
  photoError.value = null
  photoSubmitting.value = true
  try {
    await api.uploadPhoto(props.id, photoFile.value)
    await store.refresh(props.id)
  } catch (err) {
    photoError.value = err.message
  } finally {
    photoSubmitting.value = false
  }
}
</script>

<template>
  <div v-if="store.loading && !store.deal" class="muted">Loading…</div>

  <template v-else-if="store.deal">
    <div class="card">
      <div class="deal-head">
        <h1>{{ store.deal.title }}</h1>
        <span class="status-pill" :class="`tone-${statusTone}`">{{ store.deal.status }}</span>
      </div>
      <p class="price">${{ store.deal.price.toFixed(2) }}</p>
      <RiskBadge :risk-score="store.deal.risk_score" :risk-reasons="store.deal.risk_reasons" />
    </div>

    <div v-if="store.deal.status === 'CAPTURED'" class="card outcome outcome-success">
      Payment captured — the seller has been paid.
    </div>
    <div v-else-if="store.deal.status === 'VOIDED'" class="card outcome outcome-danger">
      Authorization voided — the buyer was never charged.
    </div>
    <div v-else-if="store.deal.status === 'NEEDS_HUMAN'" class="card outcome outcome-warning">
      This deal needs a human decision. Check the
      <RouterLink to="/review">review queue</RouterLink>.
    </div>

    <div v-if="store.deal.status === 'AUTHORIZED'" class="card">
      <h2>Ship panel (seller)</h2>
      <form @submit.prevent="submitTracking">
        <div class="field">
          <label for="carrier">Carrier</label>
          <input id="carrier" v-model="carrier" required placeholder="USPS, UPS, FedEx..." />
        </div>
        <div class="field">
          <label for="tracking">Tracking number</label>
          <input id="tracking" v-model="trackingNumber" required />
        </div>
        <p v-if="shipError" class="error-text">{{ shipError }}</p>
        <button class="btn btn-primary" type="submit" :disabled="shipSubmitting">
          {{ shipSubmitting ? 'Saving…' : 'Mark as shipped' }}
        </button>
      </form>
    </div>

    <div v-if="store.deal.status === 'SHIPPED'" class="card">
      <h2>Delivery (demo)</h2>
      <p class="muted">No real carrier webhook is wired up — use this to simulate delivery.</p>
      <button class="btn btn-secondary" :disabled="deliveredSubmitting" @click="markDelivered">
        {{ deliveredSubmitting ? 'Marking…' : 'Mark as delivered' }}
      </button>
    </div>

    <div v-if="store.deal.status === 'DELIVERED'" class="card">
      <h2>Upload photo (buyer)</h2>
      <p class="muted">Upload a photo of what you actually received — the Verifier compares it to the listing.</p>
      <input type="file" accept="image/*" @change="onFileChange" />
      <p v-if="photoError" class="error-text">{{ photoError }}</p>
      <button class="btn btn-primary" :disabled="!photoFile || photoSubmitting" @click="submitPhoto">
        {{ photoSubmitting ? 'Verifying…' : 'Submit photo' }}
      </button>
    </div>

    <div v-if="store.deal.buyer_photo_url" class="card">
      <h2>Received item photo</h2>
      <img class="received-photo" :src="store.deal.buyer_photo_url" alt="Buyer-uploaded photo" />
    </div>

    <div class="card">
      <h2>Agent timeline</h2>
      <AgentTimeline :decisions="store.timeline.decisions" :events="store.timeline.events" />
    </div>
  </template>
</template>

<style scoped>
.deal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

h1 {
  font-size: 1.4rem;
  margin: 0;
}

.price {
  font-weight: 700;
  color: var(--accent);
  margin: 0.25rem 0 0.75rem;
}

.status-pill.tone-neutral {
  background: var(--border);
  color: var(--text);
}

.status-pill.tone-success {
  background: var(--success-bg);
  color: var(--success);
}

.status-pill.tone-danger {
  background: var(--danger-bg);
  color: var(--danger);
}

.status-pill.tone-warning {
  background: var(--warning-bg);
  color: var(--warning);
}

.outcome {
  font-weight: 600;
}

.outcome-success {
  color: var(--success);
}

.outcome-danger {
  color: var(--danger);
}

.outcome-warning {
  color: var(--warning);
}

h2 {
  font-size: 1.05rem;
  margin: 0 0 0.75rem;
}

.card + .card {
  margin-top: 1rem;
}

.received-photo {
  max-width: 100%;
  border-radius: 8px;
}
</style>
