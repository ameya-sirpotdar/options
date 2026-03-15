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

/** Set expiry + tickers so canPoll is true. */
function setReady(composable) {
  composable.expiry.value = '2025-01-17'
  composable.tickers.value = 'AAPL'
}

describe('useMarketData', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('initializes with empty options, isPolling false, and no error', () => {
    const { options, isPolling, error } = useMarketData()
    expect(options.value).toEqual([])
    expect(isPolling.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('sets isPolling to true while fetching and false after', async () => {
    let resolvePromise
    getTrades.mockReturnValue(new Promise((res) => { resolvePromise = res }))

    const comp = useMarketData()
    setReady(comp)
    const { fetchMarketData, isPolling } = comp
    const fetchCall = fetchMarketData()

    expect(isPolling.value).toBe(true)

    resolvePromise([])
    await fetchCall
    await flushPromises()

    expect(isPolling.value).toBe(false)
  })

  it('calls getTrades when fetchMarketData is invoked', async () => {
    getTrades.mockResolvedValue([])
    const comp = useMarketData()
    setReady(comp)
    await comp.fetchMarketData()
    expect(getTrades).toHaveBeenCalledTimes(1)
  })

  it('updates options with the flat list returned from GET /trades', async () => {
    const mockTrades = [makeTrade(), makeTrade({ symbol: 'TSLA', tradability_score: 90.0 })]
    getTrades.mockResolvedValue(mockTrades)

    const comp = useMarketData()
    setReady(comp)
    await comp.fetchMarketData()
    await flushPromises()

    expect(comp.options.value).toEqual(mockTrades)
    expect(comp.options.value).toHaveLength(2)
  })

  it('exposes tradability_score on each trade item', async () => {
    const mockTrades = [makeTrade({ tradability_score: 85.3 })]
    getTrades.mockResolvedValue(mockTrades)

    const comp = useMarketData()
    setReady(comp)
    await comp.fetchMarketData()
    await flushPromises()

    expect(comp.options.value[0].tradability_score).toBe(85.3)
  })

  it('sets error and keeps options empty when getTrades throws', async () => {
    getTrades.mockRejectedValue(new Error('Network error'))

    const comp = useMarketData()
    setReady(comp)
    await comp.fetchMarketData()
    await flushPromises()

    expect(comp.error.value).toBeTruthy()
    expect(comp.options.value).toEqual([])
  })

  it('clears previous error on a successful fetch', async () => {
    getTrades.mockRejectedValueOnce(new Error('Temporary failure'))
    getTrades.mockResolvedValueOnce([makeTrade()])

    const comp = useMarketData()
    setReady(comp)

    await comp.fetchMarketData()
    await flushPromises()
    expect(comp.error.value).toBeTruthy()

    await comp.fetchMarketData()
    await flushPromises()
    expect(comp.error.value).toBeNull()
  })

  it('clears previous options on a failed fetch', async () => {
    getTrades.mockResolvedValueOnce([makeTrade()])
    getTrades.mockRejectedValueOnce(new Error('Failure'))

    const comp = useMarketData()
    setReady(comp)

    await comp.fetchMarketData()
    await flushPromises()
    expect(comp.options.value).toHaveLength(1)

    await comp.fetchMarketData()
    await flushPromises()
    expect(comp.options.value).toEqual([])
  })

  it('handles getTrades returning an empty array gracefully', async () => {
    getTrades.mockResolvedValue([])

    const comp = useMarketData()
    setReady(comp)
    await comp.fetchMarketData()
    await flushPromises()

    expect(comp.options.value).toEqual([])
    expect(comp.error.value).toBeNull()
  })

  it('handles getTrades returning null gracefully', async () => {
    getTrades.mockResolvedValue(null)

    const comp = useMarketData()
    setReady(comp)
    await comp.fetchMarketData()
    await flushPromises()

    expect(comp.options.value).toEqual([])
    expect(comp.error.value).toBeNull()
  })

  it('sets isPolling to false even when getTrades throws', async () => {
    getTrades.mockRejectedValue(new Error('Crash'))

    const comp = useMarketData()
    setReady(comp)
    await comp.fetchMarketData()
    await flushPromises()

    expect(comp.isPolling.value).toBe(false)
  })

  it('supports multiple sequential fetchMarketData calls independently', async () => {
    const firstBatch = [makeTrade({ symbol: 'AAPL' })]
    const secondBatch = [makeTrade({ symbol: 'TSLA' }), makeTrade({ symbol: 'NVDA' })]
    getTrades.mockResolvedValueOnce(firstBatch).mockResolvedValueOnce(secondBatch)

    const comp = useMarketData()
    setReady(comp)

    await comp.fetchMarketData()
    await flushPromises()
    expect(comp.options.value).toEqual(firstBatch)

    await comp.fetchMarketData()
    await flushPromises()
    expect(comp.options.value).toEqual(secondBatch)
  })
})
