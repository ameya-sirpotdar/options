import apiClient from './client.js'

export async function pollOptions({ tickers, delta, expiry }) {
  const response = await apiClient.get('/options-chain', {
    params: { tickers, delta, expiry },
    paramsSerializer: (params) => {
      const parts = []
      ;(params.tickers || []).forEach((t) => parts.push(`tickers=${encodeURIComponent(t)}`))
      if (params.delta != null) parts.push(`delta=${encodeURIComponent(params.delta)}`)
      if (params.expiry != null) parts.push(`expiry=${encodeURIComponent(params.expiry)}`)
      return parts.join('&')
    },
  })
  return response.data
}

export async function calculateTrades({ delta, expiry }) {
  const response = await apiClient.post('/trades/calculate', { delta, expiry })
  return response.data
}
