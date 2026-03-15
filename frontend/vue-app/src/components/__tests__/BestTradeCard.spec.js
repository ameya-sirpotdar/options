import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BestTradeCard from '../BestTradeCard.vue'

/**
 * Trade objects now come from GET /trades, which returns a flat list where
 * each item combines options contract fields with a tradability_score.
 */
const makeTrade = (overrides = {}) => ({
  symbol: 'AAPL',
  strike: 150.0,
  expiry: '2025-06-20',
  option_type: 'CALL',
  delta: 0.45,
  premium: 3.25,
  bid: 3.1,
  ask: 3.4,
  volume: 1200,
  open_interest: 4500,
  implied_volatility: 0.28,
  tradability_score: 87.5,
  ...overrides,
})

describe('BestTradeCard', () => {
  it('renders empty state when trade prop is null', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: null } })
    expect(wrapper.find('[data-testid="trade-empty"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="trade-content"]').exists()).toBe(false)
  })

  it('renders empty state when trade prop is undefined', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: undefined } })
    expect(wrapper.find('[data-testid="trade-empty"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="trade-content"]').exists()).toBe(false)
  })

  it('renders trade content when trade prop is provided', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade() } })
    expect(wrapper.find('[data-testid="trade-content"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="trade-empty"]').exists()).toBe(false)
  })

  it('displays the symbol correctly', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ symbol: 'TSLA' }) } })
    expect(wrapper.find('[data-testid="trade-symbol"]').text()).toContain('TSLA')
  })

  it('displays the strike price correctly', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ strike: 200.0 }) } })
    expect(wrapper.find('[data-testid="trade-strike"]').text()).toContain('200')
  })

  it('displays the expiry date correctly', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ expiry: '2025-09-19' }) } })
    expect(wrapper.find('[data-testid="trade-expiry"]').text()).toContain('2025-09-19')
  })

  it('displays the delta value correctly', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ delta: 0.45 }) } })
    expect(wrapper.find('[data-testid="trade-delta"]').text()).toContain('0.45')
  })

  it('displays the premium correctly', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ premium: 3.25 }) } })
    expect(wrapper.find('[data-testid="trade-premium"]').text()).toContain('3.25')
  })

  it('displays bid and ask prices', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ bid: 3.1, ask: 3.4 }) } })
    expect(wrapper.find('[data-testid="trade-bid"]').text()).toContain('3.1')
    expect(wrapper.find('[data-testid="trade-ask"]').text()).toContain('3.4')
  })

  it('displays volume and open interest', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ volume: 1200, open_interest: 4500 }) } })
    expect(wrapper.find('[data-testid="trade-volume"]').text()).toContain('1,200')
    expect(wrapper.find('[data-testid="trade-open-interest"]').text()).toContain('4,500')
  })

  it('displays implied volatility', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ implied_volatility: 0.28 }) } })
    expect(wrapper.find('[data-testid="trade-iv"]').text()).toContain('28.00%')
  })

  it('displays the option type', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ option_type: 'PUT' }) } })
    expect(wrapper.find('[data-testid="trade-option-type"]').text()).toContain('PUT')
  })

  it('displays the tradability score', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ tradability_score: 87.5 }) } })
    expect(wrapper.find('[data-testid="trade-score"]').text()).toContain('87.5')
  })

  it('applies a highlighted or featured card style', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade() } })
    const card = wrapper.find('[data-testid="trade-card"]')
    expect(card.exists()).toBe(true)
    // Card element should carry a CSS class that marks it as a featured/best trade
    expect(
      card.classes().some((c) => ['best-trade', 'featured', 'highlighted', 'trade-card'].includes(c))
    ).toBe(true)
  })

  it('renders a card title or heading', () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade() } })
    expect(wrapper.find('[data-testid="trade-title"]').exists()).toBe(true)
  })

  it('updates displayed values when trade prop changes', async () => {
    const wrapper = mount(BestTradeCard, { props: { trade: makeTrade({ symbol: 'AAPL' }) } })
    expect(wrapper.find('[data-testid="trade-symbol"]').text()).toContain('AAPL')

    await wrapper.setProps({ trade: makeTrade({ symbol: 'MSFT' }) })
    expect(wrapper.find('[data-testid="trade-symbol"]').text()).toContain('MSFT')
  })

  it('transitions from empty to populated when trade prop is set', async () => {
    const wrapper = mount(BestTradeCard, { props: { trade: null } })
    expect(wrapper.find('[data-testid="trade-empty"]').exists()).toBe(true)

    await wrapper.setProps({ trade: makeTrade() })
    expect(wrapper.find('[data-testid="trade-content"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="trade-empty"]').exists()).toBe(false)
  })
})
