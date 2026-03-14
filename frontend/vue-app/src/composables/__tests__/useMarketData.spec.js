import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises } from '@vue/test-utils'

// Mock the endpoints module before importing the composable
vi.mock('../../api/endpoints.js', () => ({
  getTrades: vi.fn(),
}))

import { useMarketData } from '../useMarketData.js'
import { getTrades } from '../../api/endpoints.js'

const makeTrade = (overrides = {}) => ({
  symbol: 'AAPL',
  expiration: '2025-01-17',
  strike: 200,
  option_type: 'CALL',
  bid: 1.5,
  ask: 1.6,
  volume: 1000,
  open_interest: 5000,
  delta: 0.45,
  tradability_score: 78.5,
  ...overrides,
})

describe('useMarketData', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('initializes with empty trades, isLoading false, and no error', () => {
    const { trades, isLoading, error } = useMarketData()
    expect(trades.value).toEqual([])
    expect(isLoading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('sets isLoading to true while fetching and false after', async () => {
    let resolvePromise
    getTrades.mockReturnValue(new Promise((res) => { resolvePromise = res }))

    const { fetchTrades, isLoading } = useMarketData()
    const fetchCall = fetchTrades()

    expect(isLoading.value).toBe(true)

    resolvePromise([])
    await fetchCall
    await flushPromises()

    expect(isLoading.value).toBe(false)
  })

  it('calls getTrades when fetchTrades is invoked', async () => {
    getTrades.mockResolvedValue([])
    const { fetchTrades } = useMarketData()
    await fetchTrades()
    expect(getTrades).toHaveBeenCalledTimes(1)
  })

  it('updates trades with the flat list returned from GET /trades', async () => {
    const mockTrades = [makeTrade(), makeTrade({ symbol: 'TSLA', tradability_score: 90.0 })]
    getTrades.mockResolvedValue(mockTrades)

    const { fetchTrades, trades } = useMarketData()
    await fetchTrades()
    await flushPromises()

    expect(trades.value).toEqual(mockTrades)
    expect(trades.value).toHaveLength(2)
  })

  it('exposes tradability_score on each trade item', async () => {
    const mockTrades = [makeTrade({ tradability_score: 85.3 })]
    getTrades.mockResolvedValue(mockTrades)

    const { fetchTrades, trades } = useMarketData()
    await fetchTrades()
    await flushPromises()

    expect(trades.value[0].tradability_score).toBe(85.3)
  })

  it('sets error and keeps trades empty when getTrades throws', async () => {
    getTrades.mockRejectedValue(new Error('Network error'))

    const { fetchTrades, trades, error } = useMarketData()
    await fetchTrades()
    await flushPromises()

    expect(error.value).toBeTruthy()
    expect(trades.value).toEqual([])
  })

  it('clears previous error on a successful fetch', async () => {
    getTrades.mockRejectedValueOnce(new Error('Temporary failure'))
    getTrades.mockResolvedValueOnce([makeTrade()])

    const { fetchTrades, error } = useMarketData()

    await fetchTrades()
    await flushPromises()
    expect(error.value).toBeTruthy()

    await fetchTrades()
    await flushPromises()
    expect(error.value).toBeNull()
  })

  it('clears previous trades on a failed fetch', async () => {
    getTrades.mockResolvedValueOnce([makeTrade()])
    getTrades.mockRejectedValueOnce(new Error('Failure'))

    const { fetchTrades, trades } = useMarketData()

    await fetchTrades()
    await flushPromises()
    expect(trades.value).toHaveLength(1)

    await fetchTrades()
    await flushPromises()
    expect(trades.value).toEqual([])
  })

  it('handles getTrades returning an empty array gracefully', async () => {
    getTrades.mockResolvedValue([])

    const { fetchTrades, trades, error } = useMarketData()
    await fetchTrades()
    await flushPromises()

    expect(trades.value).toEqual([])
    expect(error.value).toBeNull()
  })

  it('handles getTrades returning null gracefully', async () => {
    getTrades.mockResolvedValue(null)

    const { fetchTrades, trades, error } = useMarketData()
    await fetchTrades()
    await flushPromises()

    expect(trades.value).toEqual([])
    expect(error.value).toBeNull()
  })

  it('sets isLoading to false even when getTrades throws', async () => {
    getTrades.mockRejectedValue(new Error('Crash'))

    const { fetchTrades, isLoading } = useMarketData()
    await fetchTrades()
    await flushPromises()

    expect(isLoading.value).toBe(false)
  })

  it('supports multiple sequential fetchTrades calls independently', async () => {
    const firstBatch = [makeTrade({ symbol: 'AAPL' })]
    const secondBatch = [makeTrade({ symbol: 'TSLA' }), makeTrade({ symbol: 'NVDA' })]
    getTrades.mockResolvedValueOnce(firstBatch).mockResolvedValueOnce(secondBatch)

    const { fetchTrades, trades } = useMarketData()

    await fetchTrades()
    await flushPromises()
    expect(trades.value).toEqual(firstBatch)

    await fetchTrades()
    await flushPromises()
    expect(trades.value).toEqual(secondBatch)
  })
})
