import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import OptionsTable from '../OptionsTable.vue'

describe('OptionsTable', () => {
  const sampleOptions = [
    {
      symbol: 'SPY',
      expiry: '2024-03-15',
      strike: 450,
      type: 'call',
      bid: 2.50,
      ask: 2.55,
      mid: 2.525,
      delta: 0.30,
      iv: 0.18,
      volume: 1500,
      openInterest: 25000,
    },
    {
      symbol: 'SPY',
      expiry: '2024-03-15',
      strike: 445,
      type: 'put',
      bid: 1.80,
      ask: 1.85,
      mid: 1.825,
      delta: -0.28,
      iv: 0.20,
      volume: 800,
      openInterest: 12000,
    },
  ]

  it('renders without crashing', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: [], loading: false, vix: null },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('shows empty state message when options array is empty', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: [], loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('No options data')
  })

  it('shows loading indicator when loading prop is true', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: [], loading: true, vix: null },
    })
    expect(wrapper.text()).toContain('Loading')
  })

  it('does not show loading indicator when loading is false', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).not.toContain('Loading')
  })

  it('renders a row for each option in the options prop', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(sampleOptions.length)
  })

  it('displays strike price for each option', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('450')
    expect(wrapper.text()).toContain('445')
  })

  it('displays option type for each option', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('call')
    expect(wrapper.text()).toContain('put')
  })

  it('displays bid and ask prices', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('2.50')
    expect(wrapper.text()).toContain('2.55')
    expect(wrapper.text()).toContain('1.80')
    expect(wrapper.text()).toContain('1.85')
  })

  it('displays delta values', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('0.30')
    expect(wrapper.text()).toContain('-0.28')
  })

  it('displays implied volatility values', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('0.18')
    expect(wrapper.text()).toContain('0.20')
  })

  it('displays volume values', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('1500')
    expect(wrapper.text()).toContain('800')
  })

  it('displays VIX value when provided', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: 18.5 },
    })
    expect(wrapper.text()).toContain('18.5')
  })

  it('does not display VIX section when vix is null', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).not.toContain('VIX:')
  })

  it('renders table headers', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    const headers = wrapper.findAll('th')
    expect(headers.length).toBeGreaterThan(0)
  })

  it('renders expiry date for each option', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('2024-03-15')
  })

  it('renders open interest values', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('25000')
    expect(wrapper.text()).toContain('12000')
  })

  it('renders mid price values', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: null },
    })
    expect(wrapper.text()).toContain('2.525') || expect(wrapper.text()).toContain('2.53')
  })

  it('accepts a single option in the options array', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: [sampleOptions[0]], loading: false, vix: null },
    })
    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(1)
  })

  it('renders correctly with VIX value of zero', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: false, vix: 0 },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('shows loading state even when options are present', () => {
    const wrapper = mount(OptionsTable, {
      props: { options: sampleOptions, loading: true, vix: null },
    })
    expect(wrapper.text()).toContain('Loading')
  })
})