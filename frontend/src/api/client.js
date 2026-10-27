const BASE_URL = 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: options.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const data = await response.json()
      detail = data.detail || JSON.stringify(data)
    } catch {
      // response had no JSON body
    }
    throw new Error(detail)
  }
  if (response.status === 204) return null
  return response.json()
}

export const api = {
  createDeal: (payload) => request('/deals', { method: 'POST', body: JSON.stringify(payload) }),
  getDeal: (id) => request(`/deals/${id}`),
  createOrder: (id) => request(`/deals/${id}/order`, { method: 'POST' }),
  authorizeDeal: (id) => request(`/deals/${id}/authorize`, { method: 'POST' }),
  addTracking: (id, payload) =>
    request(`/deals/${id}/tracking`, { method: 'POST', body: JSON.stringify(payload) }),
  markDelivered: (id) => request(`/deals/${id}/delivered`, { method: 'POST' }),
  uploadPhoto: (id, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/deals/${id}/photo`, { method: 'POST', body: form })
  },
  getTimeline: (id) => request(`/deals/${id}/timeline`),
  getReviewQueue: () => request('/review'),
  resolveReview: (id, payload) =>
    request(`/review/${id}`, { method: 'POST', body: JSON.stringify(payload) }),
}

export { BASE_URL }
