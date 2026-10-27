<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import hero from '../assets/hero.png'

const router = useRouter()
const dealLink = ref('')

function goToDeal() {
  const trimmed = dealLink.value.trim()
  if (!trimmed) return
  // Accept either a bare deal id or a full /deal/<id> link someone pasted.
  const match = trimmed.match(/deal\/([a-zA-Z0-9-]+)/)
  const id = match ? match[1] : trimmed
  router.push(`/deal/${id}`)
}
</script>

<template>
  <section class="hero">
    <div class="hero-copy">
      <h1>Safe Deal Link</h1>
      <p class="pitch">
        Escrow exists but is manual and slow. We made it instant and evidence based with AI
        agents, using PayPal authorize and capture so no one ever holds the money.
      </p>
      <div class="hero-actions">
        <RouterLink to="/new" class="btn btn-primary">I'm selling</RouterLink>
        <div class="buyer-entry">
          <input
            v-model="dealLink"
            type="text"
            placeholder="Paste the deal link a seller sent you"
            @keyup.enter="goToDeal"
          />
          <button class="btn btn-secondary" @click="goToDeal">I'm buying</button>
        </div>
      </div>
    </div>
    <img :src="hero" alt="" class="hero-image" />
  </section>

  <section class="how-it-works">
    <h2>How it works</h2>
    <div class="steps">
      <div class="card step">
        <strong>1. Pay with a hold</strong>
        <p class="muted">Buyer pays with PayPal authorize — funds are held, not sent.</p>
      </div>
      <div class="card step">
        <strong>2. AI verifies delivery</strong>
        <p class="muted">Agents check the listing, tracking, and a photo of the item received.</p>
      </div>
      <div class="card step">
        <strong>3. Release or void</strong>
        <p class="muted">A match captures the payment. A mismatch voids it — nobody is ever charged by mistake.</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  display: flex;
  align-items: center;
  gap: 2.5rem;
  padding: 2rem 0 3rem;
}

.hero-copy {
  flex: 1;
}

.hero h1 {
  font-size: 2.4rem;
  margin: 0 0 1rem;
}

.pitch {
  color: var(--text-muted);
  font-size: 1.05rem;
  max-width: 44ch;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.buyer-entry {
  display: flex;
  gap: 0.5rem;
}

.buyer-entry input {
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  min-width: 260px;
}

.hero-image {
  width: 280px;
  max-width: 40vw;
  border-radius: 12px;
}

.how-it-works h2 {
  font-size: 1.3rem;
  margin-bottom: 1rem;
}

.steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.step p {
  margin: 0.5rem 0 0;
  font-size: 0.9rem;
}

@media (max-width: 720px) {
  .hero {
    flex-direction: column;
  }
  .steps {
    grid-template-columns: 1fr;
  }
}
</style>
