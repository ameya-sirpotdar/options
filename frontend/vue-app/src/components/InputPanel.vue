<template>
  <section class="input-panel" aria-label="Trade input parameters">
    <h2 class="input-panel__title">Market Parameters</h2>

    <div class="input-panel__grid">
      <!-- Row 1: Tickers, Delta, Expiry -->
      <div class="input-panel__field">
        <label class="input-panel__label">Tickers</label>
        <div class="ticker-dropdown" ref="dropdownRef">
          <button
            type="button"
            class="ticker-trigger"
            :class="{ 'ticker-trigger--open': dropdownOpen }"
            @click="dropdownOpen = !dropdownOpen"
            aria-haspopup="listbox"
            :aria-expanded="dropdownOpen"
          >
            <span class="ticker-trigger__text">
              {{ selectedTickers.length === 0 ? 'Select tickers…' : selectedTickers.join(', ') }}
            </span>
            <span class="ticker-trigger__caret">▾</span>
          </button>
          <div v-if="dropdownOpen" class="ticker-menu" role="listbox" aria-multiselectable="true">
            <div class="ticker-menu__controls">
              <button type="button" class="ticker-menu__ctrl-btn" @click="selectAll">All</button>
              <button type="button" class="ticker-menu__ctrl-btn" @click="clearAll">Clear</button>
            </div>
            <label
              v-for="ticker in defaultTickers"
              :key="ticker"
              class="ticker-menu__item"
              role="option"
              :aria-selected="selectedTickers.includes(ticker)"
            >
              <input
                type="checkbox"
                :value="ticker"
                :checked="selectedTickers.includes(ticker)"
                @change="toggleTicker(ticker)"
              />
              {{ ticker }}
            </label>
          </div>
        </div>
      </div>

      <div class="input-panel__field">
        <label for="delta-input" class="input-panel__label">Delta <span class="input-panel__delta-val">{{ localDelta != null ? Number(localDelta).toFixed(2) : '' }}</span></label>
        <div class="delta-input-wrap">
          <input
            id="delta-input"
            v-model.number="localDelta"
            type="range"
            min="0.10"
            max="0.50"
            step="0.01"
            class="input-panel__number"
            @change="emitDelta"
          />
          <button
            v-if="localDelta !== null"
            type="button"
            class="delta-clear-btn"
            aria-label="Clear delta"
            @click="clearDelta"
          >✕</button>
        </div>
      </div>

      <div class="input-panel__field">
        <label for="expiry-date" class="input-panel__label">Expiry Date</label>
        <input
          id="expiry-date"
          v-model="localExpiry"
          type="date"
          class="input-panel__date"
          :min="minDate"
          aria-required="true"
          @change="emitExpiry"
        />
      </div>

      <!-- Row 2: Option Type, VIX, Actions -->
      <div class="input-panel__field">
        <label class="input-panel__label">Option Type</label>
        <div class="segmented-btns" role="group" aria-label="Option type filter">
          <button
            v-for="opt in optionTypes"
            :key="opt.value"
            type="button"
            class="segmented-btns__btn"
            :class="{ 'segmented-btns__btn--active': localOptionType === opt.value }"
            @click="setOptionType(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <div class="input-panel__field">
        <span class="input-panel__label">
          VIX <span class="input-panel__vix-hint">(read-only)</span>
        </span>
        <div
          class="input-panel__vix-display"
          role="status"
          aria-live="polite"
          aria-label="Current VIX value"
        >
          <span v-if="vix !== null" class="input-panel__vix-value">{{ formattedVix }}</span>
          <span v-else class="input-panel__vix-placeholder">—</span>
        </div>
      </div>

      <div class="input-panel__field input-panel__field--actions">
        <label class="input-panel__label">&nbsp;</label>
        <div class="input-panel__actions">
          <button
            class="input-panel__btn input-panel__btn--primary"
            :disabled="isPollDisabled"
            :aria-busy="isPolling"
            @click="handlePoll"
          >
            <span v-if="isPolling" class="input-panel__spinner" aria-hidden="true" />
            {{ isPolling ? 'Polling…' : 'Poll Market Data' }}
          </button>
          <button
            class="input-panel__btn input-panel__btn--secondary"
            :disabled="isCalcDisabled"
            :aria-busy="isCalculating"
            @click="handleCalculate"
          >
            <span v-if="isCalculating" class="input-panel__spinner" aria-hidden="true" />
            {{ isCalculating ? 'Calculating…' : 'Calculate Trades' }}
          </button>
        </div>
      </div>
    </div>

    <p v-if="errorMessage" class="input-panel__error" role="alert">
      {{ errorMessage }}
    </p>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

const defaultTickers = ['QQQ', 'SPY', 'MSFT', 'AAPL', 'GOOG', 'META', 'NFLX', 'TSLA', 'NVDA', 'AMZN']

const optionTypes = [
  { value: 'all', label: 'All' },
  { value: 'calls', label: 'Calls' },
  { value: 'puts', label: 'Puts' },
  { value: 'straddle', label: 'Straddle' },
]

const props = defineProps({
  delta: {
    type: Number,
    default: 0.30,
  },
  expiry: {
    type: String,
    default: '',
  },
  tickers: {
    type: String,
    default: '',
  },
  optionType: {
    type: String,
    default: 'all',
  },
  vix: {
    type: Number,
    default: null,
  },
  isPolling: {
    type: Boolean,
    default: false,
  },
  isCalculating: {
    type: Boolean,
    default: false,
  },
  hasOptions: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: '',
  },
})

const emit = defineEmits([
  'update:delta',
  'update:expiry',
  'update:tickers',
  'update:optionType',
  'poll',
  'calculate',
])

// Ticker dropdown
const dropdownOpen = ref(false)
const dropdownRef = ref(null)

const selectedTickers = ref(
  props.tickers ? props.tickers.split(',').map(t => t.trim()).filter(Boolean) : []
)

watch(() => props.tickers, (val) => {
  selectedTickers.value = val ? val.split(',').map(t => t.trim()).filter(Boolean) : []
})

function toggleTicker(ticker) {
  const idx = selectedTickers.value.indexOf(ticker)
  if (idx === -1) selectedTickers.value.push(ticker)
  else selectedTickers.value.splice(idx, 1)
  emit('update:tickers', selectedTickers.value.join(', '))
}

function selectAll() {
  selectedTickers.value = [...defaultTickers]
  emit('update:tickers', selectedTickers.value.join(', '))
}

function clearAll() {
  selectedTickers.value = []
  emit('update:tickers', '')
}

function handleClickOutside(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    dropdownOpen.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', handleClickOutside))
onBeforeUnmount(() => document.removeEventListener('mousedown', handleClickOutside))

// Delta
const localDelta = ref(props.delta)
watch(() => props.delta, (val) => { localDelta.value = val })

function emitDelta() {
  emit('update:delta', localDelta.value)
}

function clearDelta() {
  localDelta.value = null
  emit('update:delta', null)
}

// Expiry
const localExpiry = ref(props.expiry)
watch(() => props.expiry, (val) => { localExpiry.value = val })

function emitExpiry() {
  emit('update:expiry', localExpiry.value)
}

// Option type
const localOptionType = ref(props.optionType)
watch(() => props.optionType, (val) => { localOptionType.value = val })

function setOptionType(val) {
  localOptionType.value = val
  emit('update:optionType', val)
}

// Computed
const formattedVix = computed(() => {
  if (props.vix === null) return '—'
  return props.vix.toFixed(2)
})

const minDate = computed(() => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return tomorrow.toISOString().split('T')[0]
})

const isPollDisabled = computed(
  () => !localExpiry.value || selectedTickers.value.length === 0 || props.isPolling || props.isCalculating,
)

const isCalcDisabled = computed(
  () => !props.hasOptions || props.isPolling || props.isCalculating,
)

function handlePoll() {
  if (isPollDisabled.value) return
  emit('poll', selectedTickers.value)
}

function handleCalculate() {
  if (isCalcDisabled.value) return
  emit('calculate')
}
</script>

<style scoped>
.input-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  box-shadow: var(--shadow-sm);
}

.input-panel__title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.input-panel__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.input-panel__field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.input-panel__field--actions {
  justify-content: flex-end;
}

.input-panel__label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 0.25rem;
}

/* ── Ticker dropdown ── */
.ticker-dropdown {
  position: relative;
}

.ticker-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  text-align: left;
  transition: border-color var(--transition-fast);
}

.ticker-trigger:hover,
.ticker-trigger--open {
  border-color: var(--color-primary);
}

.ticker-trigger__text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.ticker-trigger__caret {
  flex-shrink: 0;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.ticker-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: 100;
  overflow-y: auto;
  max-height: 280px;
}

.ticker-menu__controls {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

.ticker-menu__ctrl-btn {
  font-size: 0.75rem;
  padding: 0.2rem 0.6rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.ticker-menu__ctrl-btn:hover {
  background: var(--color-primary-muted);
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.ticker-menu__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  color: var(--color-text-primary);
  cursor: pointer;
  transition: background var(--transition-fast);
  text-transform: none;
  letter-spacing: normal;
  font-weight: 400;
}

.ticker-menu__item:hover {
  background: var(--color-primary-muted);
}

.ticker-menu__item input[type='checkbox'] {
  width: auto;
  accent-color: var(--color-primary);
  cursor: pointer;
}

/* ── Delta number input ── */
.delta-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.input-panel__number {
  width: 100%;
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  transition: border-color var(--transition-fast);
}

.input-panel__number:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-muted);
}

.delta-clear-btn {
  position: absolute;
  right: 0.5rem;
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.75rem;
  cursor: pointer;
  padding: 0.25rem;
  line-height: 1;
}

.delta-clear-btn:hover {
  color: var(--color-text-primary);
}

/* ── Date input ── */
.input-panel__date {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: 0.875rem;
  transition: border-color var(--transition-fast);
}

.input-panel__date:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-muted);
}

/* ── Segmented buttons ── */
.segmented-btns {
  display: flex;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.segmented-btns__btn {
  flex: 1;
  padding: 0.45rem 0.25rem;
  background: var(--color-surface);
  border: none;
  border-right: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.segmented-btns__btn:last-child {
  border-right: none;
}

.segmented-btns__btn:hover:not(.segmented-btns__btn--active) {
  background: var(--color-surface-raised);
  color: var(--color-text-primary);
}

.segmented-btns__btn--active {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
}

/* ── VIX ── */
.input-panel__vix-hint {
  font-size: 0.7rem;
  font-weight: 400;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
}

.input-panel__vix-display {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
  min-height: 2.25rem;
  display: flex;
  align-items: center;
}

.input-panel__vix-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  font-variant-numeric: tabular-nums;
}

.input-panel__vix-placeholder {
  font-size: 1rem;
  color: var(--color-text-muted);
}

/* ── Actions ── */
.input-panel__actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.input-panel__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.55rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: background-color var(--transition-fast), opacity var(--transition-fast);
  width: 100%;
}

.input-panel__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.input-panel__btn--primary {
  background: var(--color-primary);
  color: #fff;
}

.input-panel__btn--primary:not(:disabled):hover {
  background: var(--color-primary-hover);
}

.input-panel__btn--secondary {
  background: var(--color-surface-raised);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.input-panel__btn--secondary:not(:disabled):hover {
  background: var(--color-border);
}

.input-panel__spinner {
  display: inline-block;
  width: 0.875rem;
  height: 0.875rem;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.input-panel__error {
  font-size: 0.8125rem;
  color: var(--color-danger);
  background: var(--color-danger-muted);
  border: 1px solid rgba(224, 92, 92, 0.3);
  border-radius: var(--radius-md);
  padding: 0.5rem 0.75rem;
  margin: 0;
}

@media (max-width: 768px) {
  .input-panel__grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 480px) {
  .input-panel__grid {
    grid-template-columns: 1fr;
  }
}
</style>
