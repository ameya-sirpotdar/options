<template>
  <section class="best-trade-card" aria-label="Best Trade Candidate">
    <h2 class="card-title">Best Trade Candidate</h2>

    <div v-if="!trade" class="empty-state">
      <p class="empty-message">No trade calculated yet. Poll market data and click Calculate Trades.</p>
    </div>

    <div v-else class="trade-details">
      <div class="trade-grid">
        <div class="trade-field">
          <span class="field-label">Symbol</span>
          <span class="field-value symbol">{{ trade.symbol }}</span>
        </div>

        <div class="trade-field">
          <span class="field-label">Strike</span>
          <span class="field-value strike">${{ formatNumber(trade.strike) }}</span>
        </div>

        <div class="trade-field">
          <span class="field-label">Expiry</span>
          <span class="field-value expiry">{{ trade.expiry }}</span>
        </div>

        <div class="trade-field">
          <span class="field-label">Option Type</span>
          <span class="field-value option-type" :class="optionTypeClass">
            {{ trade.option_type ? trade.option_type.toUpperCase() : '—' }}
          </span>
        </div>

        <div class="trade-field">
          <span class="field-label">Delta</span>
          <span class="field-value delta">{{ formatDelta(trade.delta) }}</span>
        </div>

        <div class="trade-field">
          <span class="field-label">Premium</span>
          <span class="field-value premium">${{ formatNumber(trade.premium) }}</span>
        </div>

        <div class="trade-field">
          <span class="field-label">Bid</span>
          <span class="field-value bid">${{ formatNumber(trade.bid) }}</span>
        </div>

        <div class="trade-field">
          <span class="field-label">Ask</span>
          <span class="field-value ask">${{ formatNumber(trade.ask) }}</span>
        </div>

        <div class="trade-field">
          <span class="field-label">Implied Volatility</span>
          <span class="field-value iv">{{ formatPercent(trade.implied_volatility) }}</span>
        </div>

        <div class="trade-field">
          <span class="field-label">Volume</span>
          <span class="field-value volume">{{ formatInteger(trade.volume) }}</span>
        </div>

        <div class="trade-field">
          <span class="field-label">Open Interest</span>
          <span class="field-value open-interest">{{ formatInteger(trade.open_interest) }}</span>
        </div>

        <div class="trade-field score-field" v-if="trade.score !== undefined && trade.score !== null">
          <span class="field-label">Score</span>
          <span class="field-value score">{{ formatNumber(trade.score) }}</span>
        </div>
      </div>

      <div class="trade-rationale" v-if="trade.rationale">
        <h3 class="rationale-title">Rationale</h3>
        <p class="rationale-text">{{ trade.rationale }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  trade: {
    type: Object,
    default: null
  }
})

const optionTypeClass = computed(() => {
  if (!props.trade?.option_type) return ''
  return props.trade.option_type.toLowerCase() === 'call' ? 'type-call' : 'type-put'
})

function formatNumber(value) {
  if (value === undefined || value === null || value === '') return '—'
  const num = parseFloat(value)
  if (isNaN(num)) return '—'
  return num.toFixed(2)
}

function formatDelta(value) {
  if (value === undefined || value === null || value === '') return '—'
  const num = parseFloat(value)
  if (isNaN(num)) return '—'
  return num.toFixed(4)
}

function formatPercent(value) {
  if (value === undefined || value === null || value === '') return '—'
  const num = parseFloat(value)
  if (isNaN(num)) return '—'
  return (num * 100).toFixed(2) + '%'
}

function formatInteger(value) {
  if (value === undefined || value === null || value === '') return '—'
  const num = parseInt(value, 10)
  if (isNaN(num)) return '—'
  return num.toLocaleString()
}
</script>

<style scoped>
.best-trade-card {
  background-color: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 1.25rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #e2e8f0;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

.empty-message {
  color: #718096;
  font-size: 0.9rem;
  text-align: center;
  font-style: italic;
  margin: 0;
}

.trade-details {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.trade-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.trade-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.field-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field-value {
  font-size: 1rem;
  font-weight: 600;
  color: #2d3748;
}

.field-value.symbol {
  font-size: 1.125rem;
  color: #1a202c;
}

.field-value.type-call {
  color: #276749;
}

.field-value.type-put {
  color: #9b2c2c;
}

.field-value.premium,
.field-value.score {
  color: #2b6cb0;
}

.score-field {
  grid-column: span 1;
}

.trade-rationale {
  background-color: #f7fafc;
  border-left: 3px solid #4299e1;
  border-radius: 0 4px 4px 0;
  padding: 0.75rem 1rem;
}

.rationale-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #4a5568;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 0.4rem 0;
}

.rationale-text {
  font-size: 0.9rem;
  color: #4a5568;
  margin: 0;
  line-height: 1.5;
}

@media (max-width: 480px) {
  .trade-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>