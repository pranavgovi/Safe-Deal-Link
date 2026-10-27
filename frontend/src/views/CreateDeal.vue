<script setup>
import { ref } from 'vue'

import { api } from '../api/client'
import RiskBadge from '../components/RiskBadge.vue'

const title = ref('')
const description = ref('')
const price = ref('')
const sellerEmail = ref('')
const photoUrlsText = ref('')

const submitting = ref(false)
const errorMessage = ref(null)
const createdDeal = ref(null)

const shareUrl = (id) => `${window.location.origin}/deal/${id}`

async function submit() {
  errorMessage.value = null
  submitting.value = true
  try {
    const photo_urls = photoUrlsText.value
      .split(',')
      .map((url) => url.trim())
      .filter(Boolean)

    createdDeal.value = await api.createDeal({
      title: title.value,
      description: description.value,
      price: parseFloat(price.value),
      seller_email: sellerEmail.value,
      photo_urls,
    })
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    submitting.value = false
  }
}

function copyLink() {
  navigator.clipboard?.writeText(shareUrl(createdDeal.value.id))
}
</script>

<template>
  <div v-if="!createdDeal" class="card">
    <h1>List something for sale</h1>
    <p class="muted">The listing guard scores scam risk as soon as you submit — it can warn, never block.</p>

    <form @submit.prevent="submit">
      <div class="field">
        <label for="title">Title</label>
        <input id="title" v-model="title" required placeholder="iPhone 13, 128GB, like new" />
      </div>
      <div class="field">
        <label for="description">Description</label>
        <textarea id="description" v-model="description" rows="4" placeholder="Condition, accessories included, any defects..." />
      </div>
      <div class="field">
        <label for="price">Price (USD)</label>
        <input id="price" v-model="price" type="number" min="0" step="0.01" required />
      </div>
      <div class="field">
        <label for="seller-email">Your PayPal email (where you'll be paid)</label>
        <input id="seller-email" v-model="sellerEmail" type="email" required />
      </div>
      <div class="field">
        <label for="photos">Photo URLs (optional, comma separated)</label>
        <input id="photos" v-model="photoUrlsText" placeholder="https://..." />
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

      <button class="btn btn-primary" type="submit" :disabled="submitting">
        {{ submitting ? 'Creating…' : 'Create deal link' }}
      </button>
    </form>
  </div>

  <div v-else class="card">
    <h1>Deal link created</h1>
    <div class="share-row">
      <input readonly :value="shareUrl(createdDeal.id)" />
      <button class="btn btn-secondary" @click="copyLink">Copy</button>
    </div>
    <p class="muted">Send this link to the buyer. They'll pay through PayPal with the funds held, not sent.</p>

    <h3>Risk check</h3>
    <RiskBadge :risk-score="createdDeal.risk_score" :risk-reasons="createdDeal.risk_reasons" />

    <RouterLink class="btn btn-secondary view-link" :to="`/deal/${createdDeal.id}/timeline`">
      View deal timeline
    </RouterLink>
  </div>
</template>

<style scoped>
h1 {
  font-size: 1.5rem;
  margin: 0 0 0.5rem;
}

form {
  margin-top: 1.5rem;
}

.share-row {
  display: flex;
  gap: 0.5rem;
  margin: 1rem 0;
}

.share-row input {
  flex: 1;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg);
}

.view-link {
  margin-top: 1.5rem;
}
</style>
