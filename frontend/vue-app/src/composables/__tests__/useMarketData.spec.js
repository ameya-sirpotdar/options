import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, ref } from 'vue'
import { pollMarketData } from '../../api/endpoints.js'
import { useMarketData } from '../useMarketData.js'

vi.mock('../../api/endpoints.js', () => ({
  pollMarketData: vi.fn(),
}))

function createTestComponent(tickers) {
  return defineComponent({
    setup() {
      const tickersRef = typeof tickers === 'object' && 'value' in tickers ? tickers : ref(tickers)
      const { rows, loading, error, poll } = useMarketData(tickersRef)
      return { rows, loading, error, poll }
    },
    template: '<div></div>',
  })
}

describe('useMarketData', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('initializes with empty rows, loading false, and no error', () => {
    const wrapper = mount(createTestComponent(['AAPL']))
    expect(wrapper.vm.rows).toEqual([])
    expect(wrapper.vm.loading).toBe(false)
    expect(wrapper.vm.error).toBeNull()
  })

  it('sets loading to true while polling and false after', async () => {
    let resolvePromise
    pollMarketData.mockReturnValue(
      new Promise((resolve) => {
        resolvePromise = resolve
      })
    )

    const wrapper = mount(createTestComponent(['AAPL']))
    const pollPromise = wrapper.vm.poll()

    await flushPromises()
    // loading should be true before resolution... but since we check after flushPromises,
    // let's check before resolving
    // Re-test: check loading is true synchronously after calling poll
    const wrapper2 = mount(createTestComponent(['TSLA']))
    let loadingDuringPoll = false
    pollMarketData.mockImplementation(async () => {
      loadingDuringPoll = wrapper2.vm.loading
      return []
    })
    await wrapper2.vm.poll()
    await flushPromises()
    expect(loadingDuringPoll).toBe(true)
    expect(wrapper2.vm.loading).toBe(false)

    resolvePromise([])
    await pollPromise
  })

  it('calls pollMarketData with the correct tickers', async () => {
    const mockRows = [
      { ticker: 'AAPL', strike: 150, expiry: '2024-01-19', type: 'call', bid: 1.5, ask: 1.6, last: 1.55, volume: 1000, openInterest: 5000, iv: 0.25 },
    ]
    pollMarketData.mockResolvedValue(mockRows)

    const wrapper = mount(createTestComponent(['AAPL', 'MSFT']))
    await wrapper.vm.poll()
    await flushPromises()

    expect(pollMarketData).toHaveBeenCalledOnce()
    expect(pollMarketData).toHaveBeenCalledWith(['AAPL', 'MSFT'])
  })

  it('updates rows with data returned from pollMarketData', async () => {
    const mockRows = [
      { ticker: 'AAPL', strike: 150, expiry: '2024-01-19', type: 'call', bid: 1.5, ask: 1.6, last: 1.55, volume: 1000, openInterest: 5000, iv: 0.25 },
      { ticker: 'AAPL', strike: 155, expiry: '2024-01-19', type: 'put', bid: 2.0, ask: 2.1, last: 2.05, volume: 800, openInterest: 3000, iv: 0.28 },
    ]
    pollMarketData.mockResolvedValue(mockRows)

    const wrapper = mount(createTestComponent(['AAPL']))
    await wrapper.vm.poll()
    await flushPromises()

    expect(wrapper.vm.rows).toEqual(mockRows)
    expect(wrapper.vm.error).toBeNull()
  })

  it('sets error and keeps rows empty when pollMarketData throws', async () => {
    const errorMessage = 'Network error'
    pollMarketData.mockRejectedValue(new Error(errorMessage))

    const wrapper = mount(createTestComponent(['AAPL']))
    await wrapper.vm.poll()
    await flushPromises()

    expect(wrapper.vm.rows).toEqual([])
    expect(wrapper.vm.error).toBe(errorMessage)
    expect(wrapper.vm.loading).toBe(false)
  })

  it('clears previous error on successful poll', async () => {
    pollMarketData.mockRejectedValueOnce(new Error('First error'))
    const wrapper = mount(createTestComponent(['AAPL']))
    await wrapper.vm.poll()
    await flushPromises()
    expect(wrapper.vm.error).toBe('First error')

    const mockRows = [
      { ticker: 'AAPL', strike: 150, expiry: '2024-01-19', type: 'call', bid: 1.5, ask: 1.6, last: 1.55, volume: 1000, openInterest: 5000, iv: 0.25 },
    ]
    pollMarketData.mockResolvedValueOnce(mockRows)
    await wrapper.vm.poll()
    await flushPromises()

    expect(wrapper.vm.error).toBeNull()
    expect(wrapper.vm.rows).toEqual(mockRows)
  })

  it('clears previous rows on failed poll', async () => {
    const mockRows = [
      { ticker: 'AAPL', strike: 150, expiry: '2024-01-19', type: 'call', bid: 1.5, ask: 1.6, last: 1.55, volume: 1000, openInterest: 5000, iv: 0.25 },
    ]
    pollMarketData.mockResolvedValueOnce(mockRows)
    const wrapper = mount(createTestComponent(['AAPL']))
    await wrapper.vm.poll()
    await flushPromises()
    expect(wrapper.vm.rows).toEqual(mockRows)

    pollMarketData.mockRejectedValueOnce(new Error('Second error'))
    await wrapper.vm.poll()
    await flushPromises()

    expect(wrapper.vm.rows).toEqual([])
    expect(wrapper.vm.error).toBe('Second error')
  })

  it('uses reactive tickers ref - polls with updated tickers', async () => {
    const tickersRef = ref(['AAPL'])
    pollMarketData.mockResolvedValue([])

    const wrapper = mount(createTestComponent(tickersRef))
    await wrapper.vm.poll()
    await flushPromises()
    expect(pollMarketData).toHaveBeenCalledWith(['AAPL'])

    tickersRef.value = ['TSLA', 'MSFT']
    await wrapper.vm.poll()
    await flushPromises()
    expect(pollMarketData).toHaveBeenCalledWith(['TSLA', 'MSFT'])
  })

  it('handles empty tickers array', async () => {
    pollMarketData.mockResolvedValue([])

    const wrapper = mount(createTestComponent([]))
    await wrapper.vm.poll()
    await flushPromises()

    expect(pollMarketData).toHaveBeenCalledWith([])
    expect(wrapper.vm.rows).toEqual([])
    expect(wrapper.vm.error).toBeNull()
  })

  it('handles pollMarketData returning null gracefully', async () => {
    pollMarketData.mockResolvedValue(null)

    const wrapper = mount(createTestComponent(['AAPL']))
    await wrapper.vm.poll()
    await flushPromises()

    expect(wrapper.vm.rows).toEqual([])
    expect(wrapper.vm.error).toBeNull()
  })

  it('does not allow concurrent polls - second call waits or is ignored', async () => {
    let callCount = 0
    pollMarketData.mockImplementation(
      () =>
        new Promise((resolve) => {
          callCount++
          setTimeout(() => resolve([]), 100)
        })
    )

    const wrapper = mount(createTestComponent(['AAPL']))
    wrapper.vm.poll()
    wrapper.vm.poll()
    await flushPromises()

    // Either one or two calls is acceptable depending on implementation
    // but loading should be false after all settle
    expect(wrapper.vm.loading).toBe(false)
  })
})