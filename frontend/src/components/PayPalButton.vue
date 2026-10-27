<script setup>
import { loadScript } from '@paypal/paypal-js'
import { onMounted, ref } from 'vue'

import { api } from '../api/client'

const props = defineProps({
  dealId: { type: String, required: true },
})

const emit = defineEmits(['authorized', 'error'])

const container = ref(null)
const loading = ref(true)
const errorMessage = ref(null)

onMounted(async () => {
  const clientId = import.meta.env.VITE_PAYPAL_CLIENT_ID
  if (!clientId) {
    errorMessage.value = 'VITE_PAYPAL_CLIENT_ID is not set — add it to the root .env and restart the dev server.'
    loading.value = false
    return
  }

  try {
    const paypal = await loadScript({ clientId, intent: 'authorize' })

    await paypal.Buttons({
      // The SDK intent must match the backend order's intent (AUTHORIZE),
      // or PayPal rejects the approval — see build guide Phase 6.
      createOrder: async () => {
        const { order_id } = await api.createOrder(props.dealId)
        return order_id
      },
      onApprove: async () => {
        await api.authorizeDeal(props.dealId)
        emit('authorized')
      },
      onCancel: () => {
        errorMessage.value = 'Payment was cancelled.'
      },
      onError: (err) => {
        errorMessage.value = err?.message || 'PayPal checkout failed.'
        emit('error', err)
      },
    }).render(container.value)
  } catch (err) {
    errorMessage.value = err.message
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="paypal-button">
    <p v-if="loading" class="muted">Loading PayPal…</p>
    <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
    <div ref="container" />
  </div>
</template>
