import apiClient from './client.js'

export async function pollOptions({ tickers, delta, expiry }) {
  const response = await apiClient.get('/options-chain', {
    params: { tickers, delta, expiry },
  })
  return response.data
}

export async function calculateTrades({ delta, expiry }) {
  const response = await apiClient.post('/trades/calculate', { delta, expiry })
  return response.data
}
