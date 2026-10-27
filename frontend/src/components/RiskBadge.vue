<script setup>
import { computed } from 'vue'

const props = defineProps({
  riskScore: { type: Number, default: null },
  riskReasons: { type: Array, default: () => [] },
})

const level = computed(() => {
  if (props.riskScore === null || props.riskScore === undefined) return 'unknown'
  if (props.riskScore < 0.34) return 'low'
  if (props.riskScore < 0.67) return 'medium'
  return 'high'
})

const label = computed(() => {
  if (level.value === 'unknown') return 'Risk: not yet scored'
  const pct = Math.round(props.riskScore * 100)
  return `Risk: ${level.value} (${pct}%)`
})
</script>

<template>
  <div class="risk-badge" :class="`risk-${level}`">
    <span class="status-pill" :class="`risk-${level}`">{{ label }}</span>
    <ul v-if="riskReasons.length" class="risk-reasons">
      <li v-for="(reason, i) in riskReasons" :key="i">{{ reason }}</li>
    </ul>
  </div>
</template>

<style scoped>
.risk-badge {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-pill.risk-low {
  background: var(--success-bg);
  color: var(--success);
}

.status-pill.risk-medium {
  background: var(--warning-bg);
  color: var(--warning);
}

.status-pill.risk-high {
  background: var(--danger-bg);
  color: var(--danger);
}

.status-pill.risk-unknown {
  background: var(--border);
  color: var(--text-muted);
}

.risk-reasons {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}
</style>
