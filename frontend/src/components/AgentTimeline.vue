<script setup>
import { computed } from 'vue'

const props = defineProps({
  decisions: { type: Array, default: () => [] },
  events: { type: Array, default: () => [] },
})

const items = computed(() => {
  const decisionItems = props.decisions.map((d) => ({
    kind: 'decision',
    key: `d-${d.id}`,
    label: d.agent,
    action: d.action,
    detail: d.reasoning,
    confidence: d.confidence,
    createdAt: d.created_at,
  }))
  const eventItems = props.events.map((e) => ({
    kind: 'event',
    key: `e-${e.id}`,
    label: e.source,
    action: e.type,
    detail: null,
    confidence: null,
    createdAt: e.created_at,
  }))
  return [...decisionItems, ...eventItems].sort(
    (a, b) => new Date(a.createdAt) - new Date(b.createdAt),
  )
})

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString()
}
</script>

<template>
  <ol class="timeline">
    <li v-for="item in items" :key="item.key" class="timeline-item" :class="`kind-${item.kind}`">
      <div class="timeline-dot" />
      <div class="timeline-body">
        <div class="timeline-head">
          <span class="timeline-label">{{ item.label }}</span>
          <span class="timeline-action">{{ item.action }}</span>
          <span v-if="item.confidence !== null" class="timeline-confidence">
            {{ Math.round(item.confidence * 100) }}% confidence
          </span>
        </div>
        <p v-if="item.detail" class="timeline-detail">{{ item.detail }}</p>
        <time class="timeline-time">{{ formatTime(item.createdAt) }}</time>
      </div>
    </li>
    <li v-if="!items.length" class="muted">No activity yet.</li>
  </ol>
</template>

<style scoped>
.timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.timeline-item {
  display: flex;
  gap: 0.75rem;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 0.4rem;
  flex-shrink: 0;
  background: var(--accent);
}

.kind-event .timeline-dot {
  background: var(--text-muted);
}

.timeline-body {
  flex: 1;
  border-bottom: 1px solid var(--border);
  padding-bottom: 1rem;
}

.timeline-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.5rem;
}

.timeline-label {
  font-weight: 700;
  text-transform: capitalize;
}

.timeline-action {
  color: var(--text-muted);
  font-size: 0.9rem;
}

.timeline-confidence {
  font-size: 0.78rem;
  color: var(--accent);
  margin-left: auto;
}

.timeline-detail {
  margin: 0.35rem 0 0;
  font-size: 0.92rem;
}

.timeline-time {
  display: block;
  margin-top: 0.35rem;
  font-size: 0.78rem;
  color: var(--text-muted);
}
</style>
