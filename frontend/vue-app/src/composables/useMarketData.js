import { ref, computed } from 'vue'
import { getTrades } from '../api/endpoints.js'

export function useMarketData() {
  const delta = ref(0.30)
  const expiry = ref('')
  const tickers = ref('')
  const optionType = ref('all')
  const vix = ref(null)
  const options = ref([])
  const bestTrade = ref(null)
  const isPolling = ref(false)
  const error = ref(null)

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

  async function fetchMarketData() {
    if (!canPoll.value) return

    isPolling.value = true
    error.value = null
    options.value = []
    vix.value = null
    bestTrade.value = null

    try {
      // Parse comma-separated string into array before sending to API
      const tickerArray = tickers.value
        .split(',')
        .map(t => t.trim())
        .filter(Boolean)

      // GET /trades returns a flat list of trade objects with tradability scores
      const trades = await getTrades({
        tickers: tickerArray,
        delta: delta.value,
        expiry: expiry.value,
      })

      options.value = Array.isArray(trades) ? trades : []

      // Derive vix from the first trade entry if available
      vix.value = options.value.length > 0 ? (options.value[0].vix ?? null) : null

      // Best trade is the entry with the highest tradability score
      if (options.value.length > 0) {
        bestTrade.value = options.value.reduce((best, trade) => {
          const bestScore = best?.tradability_score ?? -Infinity
          const tradeScore = trade?.tradability_score ?? -Infinity
          return tradeScore > bestScore ? trade : best
        }, null)
      }
    } catch (err) {
      error.value =
        err?.response?.data?.detail ??
        err?.message ??
        'Failed to fetch market data.'
    } finally {
      isPolling.value = false
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
    error.value = null
    isPolling.value = false
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
    error,
    hasOptions,
    hasBestTrade,
    canPoll,
    fetchMarketData,
    resetAll,
  }
}
