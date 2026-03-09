frontend/vue-app/src/api/endpoints.js
import { apiClient } from './client.js'

export async function pollOptions({ delta, expiry }) {
  const response = await apiClient.get('/options/poll', {
    params: { delta, expiry },
  })
  return response.data
}

export async function calculateTrades({ delta, expiry }) {
  const response = await apiClient.post('/trades/calculate', { delta, expiry })
  return response.data
}