<template>
  <div class="app-container">
    <header class="app-header">
      <h1>Options Trade Analyzer</h1>
      <p class="subtitle">E2E Validation Demo</p>
    </header>

    <main class="app-main">
      <InputPanel
        :delta="delta"
        :expiry="expiry"
        :vix="vix"
        :tickers="tickers"
        :optionType="optionType"
        :isPolling="polling"
        :isCalculating="calculating"
        :hasOptions="hasOptions"
        @update:delta="delta = $event"
        @update:expiry="expiry = $event"
        @update:tickers="tickers = $event"
        @update:optionType="optionType = $event"
        @poll="handlePoll"
        @calculate="handleCalculate"
      />

      <section v-if="pollError" class="error-banner" role="alert">
        <span class="error-icon">⚠</span>
        <span>{{ pollError }}</span>
        <button class="dismiss-btn" @click="pollError = null">✕</button>
      </section>

      <section v-if="calculateError" class="error-banner" role="alert">
        <span class="error-icon">⚠</span>
        <span>{{ calculateError }}</span>
        <button class="dismiss-btn" @click="calculateError = null">✕</button>
      </section>

      <OptionsTable
        :rows="filteredOptions"
        :straddleRows="straddleRows"
        :optionType="optionType"
        :loading="polling"
      />

      <BestTradeCard
        :trade="bestTrade"
        :loading="calculating"
      />
    </main>

    <footer class="app-footer">
      <p>Options Trade Analyzer — Demo UI</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import InputPanel from './components/InputPanel.vue'
import OptionsTable from './components/OptionsTable.vue'
import BestTradeCard from './components/BestTradeCard.vue'
import { useMarketData } from './composables/useMarketData.js'

const {
  delta,
  expiry,
  vix,
  tickers,
  optionType,
  options,
  filteredOptions,
  straddleRows,
  hasOptions,
  bestTrade,
  isPolling: polling,
  isCalculating: calculating,
  fetchMarketData: pollOptions,
  fetchBestTrade: calculateTrades,
} = useMarketData()

const pollError = ref(null)
const calculateError = ref(null)

async function handlePoll() {
  pollError.value = null
  try {
    await pollOptions()
  } catch (err) {
    pollError.value = err?.message ?? 'Failed to poll market data. Please try again.'
  }
}

async function handleCalculate() {
  calculateError.value = null
  try {
    await calculateTrades()
  } catch (err) {
    calculateError.value = err?.message ?? 'Failed to calculate trades. Please try again.'
  }
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--color-background, #f8f9fa);
}

.app-header {
  background-color: var(--color-primary, #1a1a2e);
  color: #ffffff;
  padding: 1.5rem 2rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.app-header h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.subtitle {
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
  opacity: 0.75;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 2rem;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background-color: #fff3cd;
  border: 1px solid #ffc107;
  border-left: 4px solid #e85d04;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  color: #664d03;
  font-size: 0.9rem;
}

.error-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.dismiss-btn {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #664d03;
  font-size: 1rem;
  padding: 0 0.25rem;
  line-height: 1;
  flex-shrink: 0;
}

.dismiss-btn:hover {
  color: #3d2b00;
}

.app-footer {
  background-color: var(--color-primary, #1a1a2e);
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  padding: 1rem 2rem;
  font-size: 0.8rem;
}

.app-footer p {
  margin: 0;
}

@media (max-width: 600px) {
  .app-main {
    padding: 1rem;
    gap: 1rem;
  }

  .app-header h1 {
    font-size: 1.4rem;
  }
}
</style>