<template>
  <section class="input-panel" aria-label="Trade input parameters">
    <h2 class="input-panel__title">Market Parameters</h2>

    <div class="input-panel__field">
      <label for="delta-slider" class="input-panel__label">
        Delta
        <span class="input-panel__value-badge">{{ formattedDelta }}</span>
      </label>
      <input
        id="delta-slider"
        v-model.number="localDelta"
        type="range"
        min="0.10"
        max="0.50"
        step="0.01"
        class="input-panel__slider"
        aria-valuemin="0.10"
        aria-valuemax="0.50"
        :aria-valuenow="localDelta"
        :aria-valuetext="formattedDelta"
        @change="emitDelta"
      />
      <div class="input-panel__slider-bounds" aria-hidden="true">
        <span>0.10</span>
        <span>0.50</span>
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

    <div class="input-panel__field">
      <span class="input-panel__label">
        VIX
        <span class="input-panel__vix-hint">(read-only)</span>
      </span>
      <div
        class="input-panel__vix-display"
        role="status"
        aria-live="polite"
        aria-label="Current VIX value"
      >
        <span v-if="vix !== null" class="input-panel__vix-value">
          {{ formattedVix }}
        </span>
        <span v-else class="input-panel__vix-placeholder">—</span>
      </div>
    </div>

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

    <p v-if="errorMessage" class="input-panel__error" role="alert">
      {{ errorMessage }}
    </p>
  </section>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  delta: {
    type: Number,
    default: 0.30,
  },
  expiry: {
    type: String,
    default: '',
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
  'poll',
  'calculate',
])

const localDelta = ref(props.delta)
const localExpiry = ref(props.expiry)

watch(
  () => props.delta,
  (val) => {
    localDelta.value = val
  },
)

watch(
  () => props.expiry,
  (val) => {
    localExpiry.value = val
  },
)

const formattedDelta = computed(() => localDelta.value.toFixed(2))

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
  () => !localExpiry.value || props.isPolling || props.isCalculating,
)

const isCalcDisabled = computed(
  () => !props.hasOptions || props.isPolling || props.isCalculating,
)

function emitDelta() {
  emit('update:delta', localDelta.value)
}

function emitExpiry() {
  emit('update:expiry', localExpiry.value)
}

function handlePoll() {
  if (isPollDisabled.value) return
  emit('poll')
}

function handleCalculate() {
  if (isCalcDisabled.value) return
  emit('calculate')
}
</script>

<style scoped>
.input-panel {
  background: var(--color-surface, #ffffff);
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.75rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.input-panel__title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-text-primary, #1a202c);
  margin: 0;
}

.input-panel__field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.input-panel__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary, #4a5568);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.input-panel__value-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent, #3b82f6);
  color: #ffffff;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  min-width: 2.5rem;
}

.input-panel__slider {
  width: 100%;
  accent-color: var(--color-accent, #3b82f6);
  cursor: pointer;
  height: 0.375rem;
}

.input-panel__slider-bounds {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--color-text-muted, #718096);
}

.input-panel__date {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--color-text-primary, #1a202c);
  background: var(--color-surface, #ffffff);
  box-sizing: border-box;
  transition: border-color 0.15s ease;
}

.input-panel__date:focus {
  outline: none;
  border-color: var(--color-accent, #3b82f6);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.input-panel__vix-hint {
  font-size: 0.75rem;
  font-weight: 400;
  color: var(--color-text-muted, #718096);
}

.input-panel__vix-display {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border, #e2e8f0);
  border-radius: 0.5rem;
  background: var(--color-surface-muted, #f7fafc);
  min-height: 2.25rem;
  display: flex;
  align-items: center;
}

.input-panel__vix-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary, #1a202c);
  font-variant-numeric: tabular-nums;
}

.input-panel__vix-placeholder {
  font-size: 1rem;
  color: var(--color-text-muted, #718096);
}

.input-panel__actions {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.input-panel__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.625rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: background-color 0.15s ease, opacity 0.15s ease;
  width: 100%;
}

.input-panel__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-panel__btn--primary {
  background: var(--color-accent, #3b82f6);
  color: #ffffff;
}

.input-panel__btn--primary:not(:disabled):hover {
  background: var(--color-accent-hover, #2563eb);
}

.input-panel__btn--secondary {
  background: var(--color-surface-muted, #f7fafc);
  color: var(--color-text-primary, #1a202c);
  border: 1px solid var(--color-border, #e2e8f0);
}

.input-panel__btn--secondary:not(:disabled):hover {
  background: var(--color-border, #e2e8f0);
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
  to {
    transform: rotate(360deg);
  }
}

.input-panel__error {
  font-size: 0.8125rem;
  color: var(--color-error, #e53e3e);
  background: var(--color-error-bg, #fff5f5);
  border: 1px solid var(--color-error-border, #fed7d7);
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  margin: 0;
}
</style>