frontend/vue-app/src/components/__tests__/BestTradeCard.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BestTradeCard from '../BestTradeCard.vue'

describe('BestTradeCard', () => {
  it('renders empty state when trade prop is null', () => {
    const wrapper = mount(BestTradeCard, {
      props: { trade: null }
    })
    expect(wrapper.find('[data-testid="best-trade-empty"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="best-trade-content"]').exists()).toBe(false)
  })

  it('renders empty state when trade prop is undefined', () => {
    const wrapper = mount(BestTradeCard, {
      props: {}
    })
    expect(wrapper.find('[data-testid="best-trade-empty"]').exists()).toBe(true)
  })

  it('renders trade content when trade prop is provided', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="best-trade-empty"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="best-trade-content"]').exists()).toBe(true)
  })

  it('displays the symbol correctly', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="trade-symbol"]').text()).toContain('SPY')
  })

  it('displays the strike price correctly', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="trade-strike"]').text()).toContain('420')
  })

  it('displays the expiry date correctly', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="trade-expiry"]').text()).toContain('2024-03-15')
  })

  it('displays the delta value correctly', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="trade-delta"]').text()).toContain('0.3')
  })

  it('displays the premium correctly', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="trade-premium"]').text()).toContain('2.45')
  })

  it('displays bid and ask prices', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="trade-bid"]').text()).toContain('2.40')
    expect(wrapper.find('[data-testid="trade-ask"]').text()).toContain('2.50')
  })

  it('displays volume and open interest', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="trade-volume"]').text()).toContain('1500')
    expect(wrapper.find('[data-testid="trade-open-interest"]').text()).toContain('8000')
  })

  it('displays implied volatility', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="trade-iv"]').text()).toContain('0.22')
  })

  it('displays the option type', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="trade-type"]').text()).toContain('put')
  })

  it('applies a highlighted or featured card style', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    const card = wrapper.find('[data-testid="best-trade-card"]')
    expect(card.exists()).toBe(true)
    expect(card.classes().join(' ')).toMatch(/best-trade|highlight|featured/)
  })

  it('renders a card title or heading', () => {
    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade }
    })
    expect(wrapper.find('[data-testid="best-trade-title"]').exists()).toBe(true)
  })

  it('updates displayed values when trade prop changes', async () => {
    const trade1 = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    const wrapper = mount(BestTradeCard, {
      props: { trade: trade1 }
    })
    expect(wrapper.find('[data-testid="trade-strike"]').text()).toContain('420')

    const trade2 = { ...trade1, strike: 430, premium: 1.95 }
    await wrapper.setProps({ trade: trade2 })
    expect(wrapper.find('[data-testid="trade-strike"]').text()).toContain('430')
    expect(wrapper.find('[data-testid="trade-premium"]').text()).toContain('1.95')
  })

  it('transitions from empty to populated when trade prop is set', async () => {
    const wrapper = mount(BestTradeCard, {
      props: { trade: null }
    })
    expect(wrapper.find('[data-testid="best-trade-empty"]').exists()).toBe(true)

    const trade = {
      symbol: 'SPY',
      strike: 420,
      expiry: '2024-03-15',
      delta: 0.3,
      premium: 2.45,
      bid: 2.40,
      ask: 2.50,
      volume: 1500,
      openInterest: 8000,
      impliedVolatility: 0.22,
      type: 'put'
    }
    await wrapper.setProps({ trade })
    expect(wrapper.find('[data-testid="best-trade-empty"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="best-trade-content"]').exists()).toBe(true)
  })
})