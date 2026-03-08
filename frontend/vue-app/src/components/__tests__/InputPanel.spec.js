import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import InputPanel from '../InputPanel.vue'

describe('InputPanel', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(InputPanel, {
      props: {
        delta: 0.30,
        expiry: '2024-12-20',
        vix: null,
        loading: false,
      },
    })
  })

  it('renders the component', () => {
    expect(wrapper.exists()).toBe(true)
  })

  it('displays the delta slider with correct initial value', () => {
    const slider = wrapper.find('input[type="range"]')
    expect(slider.exists()).toBe(true)
    expect(slider.element.value).toBe('0.3')
  })

  it('displays the delta slider with correct min and max attributes', () => {
    const slider = wrapper.find('input[type="range"]')
    expect(slider.attributes('min')).toBe('0.10')
    expect(slider.attributes('max')).toBe('0.50')
  })

  it('displays the delta slider with correct step attribute', () => {
    const slider = wrapper.find('input[type="range"]')
    expect(slider.attributes('step')).toBe('0.01')
  })

  it('emits update:delta when slider value changes', async () => {
    const slider = wrapper.find('input[type="range"]')
    await slider.setValue('0.25')
    const emitted = wrapper.emitted('update:delta')
    expect(emitted).toBeTruthy()
    expect(emitted[0][0]).toBe(0.25)
  })

  it('displays the expiry date picker', () => {
    const datePicker = wrapper.find('input[type="date"]')
    expect(datePicker.exists()).toBe(true)
    expect(datePicker.element.value).toBe('2024-12-20')
  })

  it('emits update:expiry when date picker value changes', async () => {
    const datePicker = wrapper.find('input[type="date"]')
    await datePicker.setValue('2025-01-17')
    const emitted = wrapper.emitted('update:expiry')
    expect(emitted).toBeTruthy()
    expect(emitted[0][0]).toBe('2025-01-17')
  })

  it('displays VIX as N/A when vix prop is null', () => {
    expect(wrapper.text()).toContain('N/A')
  })

  it('displays VIX value when vix prop is provided', async () => {
    await wrapper.setProps({ vix: 18.45 })
    expect(wrapper.text()).toContain('18.45')
  })

  it('renders the Poll Market Data button', () => {
    const buttons = wrapper.findAll('button')
    const pollButton = buttons.find(b => b.text().includes('Poll Market Data'))
    expect(pollButton).toBeTruthy()
  })

  it('renders the Calculate Trades button', () => {
    const buttons = wrapper.findAll('button')
    const calcButton = buttons.find(b => b.text().includes('Calculate Trades'))
    expect(calcButton).toBeTruthy()
  })

  it('emits poll event when Poll Market Data button is clicked', async () => {
    const buttons = wrapper.findAll('button')
    const pollButton = buttons.find(b => b.text().includes('Poll Market Data'))
    await pollButton.trigger('click')
    expect(wrapper.emitted('poll')).toBeTruthy()
  })

  it('emits calculate event when Calculate Trades button is clicked', async () => {
    const buttons = wrapper.findAll('button')
    const calcButton = buttons.find(b => b.text().includes('Calculate Trades'))
    await calcButton.trigger('click')
    expect(wrapper.emitted('calculate')).toBeTruthy()
  })

  it('disables both buttons when loading is true', async () => {
    await wrapper.setProps({ loading: true })
    const buttons = wrapper.findAll('button')
    buttons.forEach(button => {
      expect(button.attributes('disabled')).toBeDefined()
    })
  })

  it('enables both buttons when loading is false', () => {
    const buttons = wrapper.findAll('button')
    buttons.forEach(button => {
      expect(button.attributes('disabled')).toBeUndefined()
    })
  })

  it('shows loading indicator when loading is true', async () => {
    await wrapper.setProps({ loading: true })
    expect(wrapper.text()).toMatch(/loading|Loading|spinner/i)
  })

  it('displays current delta value as formatted text', () => {
    expect(wrapper.text()).toContain('0.30')
  })

  it('updates displayed delta value when slider changes', async () => {
    const slider = wrapper.find('input[type="range"]')
    await slider.setValue('0.45')
    const emitted = wrapper.emitted('update:delta')
    expect(emitted[0][0]).toBe(0.45)
  })

  it('renders VIX label', () => {
    expect(wrapper.text()).toMatch(/vix/i)
  })

  it('renders delta label', () => {
    expect(wrapper.text()).toMatch(/delta/i)
  })

  it('renders expiry label', () => {
    expect(wrapper.text()).toMatch(/expiry/i)
  })
})