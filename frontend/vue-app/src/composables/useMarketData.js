import { ref, computed } from 'vue'
import { pollOptions, calculateTrades } from '../api/endpoints.js'

export function useMarketData() {
  const delta = ref(0.30)
  const expiry = ref('')
  const tickers = ref('')
  const optionType = ref('all')
  const vix = ref(null)
  const options = ref([])
  const bestTrade = ref(null)
  const isPolling = ref(false)
  const isCalculating = ref(false)
  const pollError = ref(null)
  const calcError = ref(null)

  const hasOptions = computed(() => options.value.length > 0)

  const filteredOptions = computed(() => {
    if (optionType.value === 'all' || optionType.value === 'straddle') return options.value
    return options.value.filter(r => r.type && r.type.toLowerCase() === optionType.value)
  })

  const straddleRows = computed(() => {
    // Group by ticker+expiry+strike and pair calls with puts
    const map = new Map()
    for (const row of options.value) {
      const key = `${row.ticker}|${row.expiry}|${row.strike}`
      if (!map.has(key)) map.set(key, { ticker: row.ticker, expiry: row.expiry, strike: row.strike, call: null, put: null })
      const t = row.type ? row.type.toLowerCase() : ''
      if (t === 'call') map.get(key).call = row
      else if (t === 'put') map.get(key).put = row
    }
    return Array.from(map.values())
  })
  const hasBestTrade = computed(() => bestTrade.value !== null)
  const canPoll = computed(
    () => expiry.value !== '' && tickers.value.length > 0 && !isPolling.value
  )
  const canCalculate = computed(() => hasOptions.value && !isCalculating.value)

  async function fetchMarketData() {
    if (!canPoll.value) return

    isPolling.value = true
    pollError.value = null
    options.value = []
    vix.value = null
    bestTrade.value = null

    try {
      // Parse comma-separated string into array before sending to API
      const tickerArray = tickers.value
        .split(',')
        .map(t => t.trim())
        .filter(Boolean)
      const response = await pollOptions({
        tickers: tickerArray,
        delta: delta.value,
        expiry: expiry.value,
      })

      // Backend returns { rows: [...], vix: number }
      options.value = response.rows ?? response.options ?? []
      vix.value = response.vix ?? null
    } catch (err) {
      pollError.value =
        err?.response?.data?.detail ??
        err?.message ??
        'Failed to fetch market data.'
    } finally {
      isPolling.value = false
    }
  }

  async function fetchBestTrade() {
    if (!canCalculate.value) return

    isCalculating.value = true
    calcError.value = null
    bestTrade.value = null

    try {
      const response = await calculateTrades({
        delta: delta.value,
        expiry: expiry.value,
        options: options.value,
        vix: vix.value,
      })

      bestTrade.value = response.best_trade ?? response ?? null
    } catch (err) {
      calcError.value =
        err?.response?.data?.detail ??
        err?.message ??
        'Failed to calculate trades.'
    } finally {
      isCalculating.value = false
    }
  }

  function resetAll() {
    delta.value = 0.30
    expiry.value = ''
    tickers.value = ''
    optionType.value = 'all'
    vix.value = null
    options.value = []
    bestTrade.value = null
    pollError.value = null
    calcError.value = null
    isPolling.value = false
    isCalculating.value = false
  }

  return {
    delta,
    expiry,
    tickers,
    optionType,
    vix,
    options,
    filteredOptions,
    straddleRows,
    bestTrade,
    isPolling,
    isCalculating,
    pollError,
    calcError,
    hasOptions,
    hasBestTrade,
    canPoll,
    canCalculate,
    fetchMarketData,
    fetchBestTrade,
    resetAll,
  }
}
