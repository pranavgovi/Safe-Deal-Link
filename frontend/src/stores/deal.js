import { defineStore } from 'pinia'

import { api } from '../api/client'

const POLL_INTERVAL_MS = 3000

export const useDealStore = defineStore('deal', {
  state: () => ({
    deal: null,
    timeline: { decisions: [], events: [] },
    loading: false,
    error: null,
    _pollHandle: null,
  }),

  getters: {
    status: (state) => state.deal?.status ?? null,
  },

  actions: {
    async fetchDeal(id) {
      this.loading = true
      this.error = null
      try {
        this.deal = await api.getDeal(id)
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async fetchTimeline(id) {
      try {
        this.timeline = await api.getTimeline(id)
      } catch (err) {
        this.error = err.message
      }
    },

    async refresh(id) {
      await Promise.all([this.fetchDeal(id), this.fetchTimeline(id)])
    },

    startPolling(id) {
      this.stopPolling()
      this._pollHandle = setInterval(() => this.refresh(id), POLL_INTERVAL_MS)
    },

    stopPolling() {
      if (this._pollHandle) {
        clearInterval(this._pollHandle)
        this._pollHandle = null
      }
    },
  },
})
