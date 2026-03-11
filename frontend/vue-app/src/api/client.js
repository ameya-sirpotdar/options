import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
  headers: {
    Accept: 'application/json',
  },
})

export function fetchOptionsChain(tickerArray) {
  return apiClient.get('/options-chain', {
    params: { tickers: tickerArray },
    paramsSerializer: (params) => {
      return params.tickers.map((t) => `tickers=${encodeURIComponent(t)}`).join('&')
    },
  })
}

apiClient.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'

    const enhancedError = new Error(message)
    enhancedError.status = error.response?.status
    enhancedError.originalError = error

    return Promise.reject(enhancedError)
  }
)

export default apiClient