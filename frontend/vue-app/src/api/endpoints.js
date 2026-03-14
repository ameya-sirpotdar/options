import apiClient from './client.js'

export async function getTrades({ delta, expiry } = {}) {
  const response = await apiClient.get('/trades', {
    params: { delta, expiry },
  })
  return response.data
}
