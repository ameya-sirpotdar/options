<template>
  <section class="options-table-section" aria-label="Options poll results">
    <h2 class="section-title">Options Chain</h2>

    <div v-if="loading" class="state-message loading" role="status" aria-live="polite">
      <span class="spinner" aria-hidden="true"></span>
      Loading options data…
    </div>

    <div v-else-if="error" class="state-message error" role="alert" aria-live="assertive">
      <span class="error-icon" aria-hidden="true">⚠</span>
      {{ error }}
    </div>

    <div v-else-if="!rows || rows.length === 0" class="state-message empty" role="status">
      No options data yet. Adjust parameters and click <strong>Poll Market Data</strong>.
    </div>

    <div v-else class="table-wrapper" role="region" aria-label="Options data table">
      <table class="options-table" aria-describedby="table-caption">
        <caption id="table-caption" class="visually-hidden">
          Options chain data with {{ rows.length }} contracts
        </caption>
        <thead>
          <tr>
            <th scope="col" class="col-ticker">Ticker</th>
            <th scope="col" class="col-expiry">Expiry</th>
            <th scope="col" class="col-strike">Strike</th>
            <th scope="col" class="col-type">Type</th>
            <th scope="col" class="col-bid">Bid</th>
            <th scope="col" class="col-ask">Ask</th>
            <th scope="col" class="col-mid">Mid</th>
            <th scope="col" class="col-delta">Delta</th>
            <th scope="col" class="col-iv">IV</th>
            <th scope="col" class="col-volume">Volume</th>
            <th scope="col" class="col-oi">Open Int.</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, index) in rows"
            :key="rowKey(row, index)"
            :class="rowClass(row)"
            :aria-label="`${row.type || 'Option'} contract: strike ${row.strike}, expiry ${row.expiry}`"
          >
            <td class="col-ticker" data-label="Ticker">
              {{ row.ticker || '—' }}
            </td>
            <td class="col-expiry" data-label="Expiry">
              {{ formatDate(row.expiry) }}
            </td>
            <td class="col-strike" data-label="Strike">
              {{ formatCurrency(row.strike) }}
            </td>
            <td class="col-type" data-label="Type">
              <span :class="['badge', typeBadgeClass(row.type)]">
                {{ row.type ? row.type.toUpperCase() : '—' }}
              </span>
            </td>
            <td class="col-bid" data-label="Bid">
              {{ formatCurrency(row.bid) }}
            </td>
            <td class="col-ask" data-label="Ask">
              {{ formatCurrency(row.ask) }}
            </td>
            <td class="col-mid" data-label="Mid">
              <strong>{{ formatCurrency(row.mid) }}</strong>
            </td>
            <td class="col-delta" data-label="Delta">
              <span :class="deltaClass(row.delta)">
                {{ formatDecimal(row.delta, 3) }}
              </span>
            </td>
            <td class="col-iv" data-label="IV">
              {{ formatPercent(row.iv) }}
            </td>
            <td class="col-volume" data-label="Volume">
              {{ formatInteger(row.volume) }}
            </td>
            <td class="col-oi" data-label="Open Int.">
              {{ formatInteger(row.open_interest) }}
            </td>
          </tr>
        </tbody>
      </table>

      <div class="table-footer">
        <span class="row-count">{{ rows.length }} contract{{ rows.length !== 1 ? 's' : '' }}</span>
        <span v-if="vix !== null && vix !== undefined" class="vix-badge" aria-label="Current VIX value">
          VIX: <strong>{{ formatDecimal(vix, 2) }}</strong>
        </span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rows: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: null,
  },
  vix: {
    type: Number,
    default: null,
  },
})

// ── Helpers ──────────────────────────────────────────────────────────────────

function rowKey(row, index) {
  if (row.ticker && row.strike && row.expiry && row.type) {
    return `${row.ticker}-${row.type}-${row.strike}-${row.expiry}`
  }
  return index
}

function rowClass(row) {
  return {
    'row-call': row.type && row.type.toLowerCase() === 'call',
    'row-put': row.type && row.type.toLowerCase() === 'put',
  }
}

function typeBadgeClass(type) {
  if (!type) return ''
  const t = type.toLowerCase()
  if (t === 'call') return 'badge-call'
  if (t === 'put') return 'badge-put'
  return ''
}

function deltaClass(delta) {
  if (delta === null || delta === undefined) return ''
  const abs = Math.abs(delta)
  if (abs >= 0.40) return 'delta-high'
  if (abs >= 0.25) return 'delta-mid'
  return 'delta-low'
}

// ── Formatters ────────────────────────────────────────────────────────────────

function formatCurrency(value) {
  if (value === null || value === undefined || value === '') return '—'
  const num = Number(value)
  if (isNaN(num)) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num)
}

function formatDecimal(value, digits = 2) {
  if (value === null || value === undefined || value === '') return '—'
  const num = Number(value)
  if (isNaN(num)) return '—'
  return num.toFixed(digits)
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') return '—'
  const num = Number(value)
  if (isNaN(num)) return '—'
  return `${(num * 100).toFixed(1)}%`
}

function formatInteger(value) {
  if (value === null || value === undefined || value === '') return '—'
  const num = Number(value)
  if (isNaN(num)) return '—'
  return new Intl.NumberFormat('en-US').format(Math.round(num))
}

function formatDate(value) {
  if (!value) return '—'
  try {
    const date = new Date(value)
    if (isNaN(date.getTime())) return value
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: 'UTC',
    }).format(date)
  } catch {
    return value
  }
}
</script>

<style scoped>
/* ── Section wrapper ─────────────────────────────────────────────────────── */
.options-table-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-heading, #1e293b);
  margin: 0;
}

/* ── State messages ──────────────────────────────────────────────────────── */
.state-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1.25rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  color: var(--color-text-muted, #64748b);
  background: var(--color-surface-alt, #f8fafc);
  border: 1px solid var(--color-border, #e2e8f0);
}

.state-message.loading {
  color: var(--color-primary, #3b82f6);
}

.state-message.error {
  color: var(--color-error, #dc2626);
  background: #fef2f2;
  border-color: #fecaca;
}

.state-message.empty {
  justify-content: center;
  text-align: center;
}

/* ── Spinner ─────────────────────────────────────────────────────────────── */
.spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── Table wrapper ───────────────────────────────────────────────────────── */
.table-wrapper {
  overflow-x: auto;
  border-radius: 0.5rem;
  border: 1px solid var(--color-border, #e2e8f0);
  background: var(--color-surface, #ffffff);
}

/* ── Table base ──────────────────────────────────────────────────────────── */
.options-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  white-space: nowrap;
}

.options-table thead {
  background: var(--color-surface-alt, #f8fafc);
  position: sticky;
  top: 0;
  z-index: 1;
}

.options-table th {
  padding: 0.625rem 0.875rem;
  text-align: right;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, #64748b);
  border-bottom: 2px solid var(--color-border, #e2e8f0);
}

.options-table th.col-ticker,
.options-table th.col-expiry,
.options-table th.col-type {
  text-align: left;
}

.options-table td {
  padding: 0.5rem 0.875rem;
  text-align: right;
  color: var(--color-text, #334155);
  border-bottom: 1px solid var(--color-border-light, #f1f5f9);
}

.options-table td.col-ticker,
.options-table td.col-expiry,
.options-table td.col-type {
  text-align: left;
}

.options-table tbody tr:last-child td {
  border-bottom: none;
}

.options-table tbody tr:hover {
  background: var(--color-surface-hover, #f0f9ff);
}

/* ── Row type tints ──────────────────────────────────────────────────────── */
.row-call {
  background: rgba(34, 197, 94, 0.03);
}

.row-put {
  background: rgba(239, 68, 68, 0.03);
}

/* ── Type badge ──────────────────────────────────────────────────────────── */
.badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.badge-call {
  background: #dcfce7;
  color: #15803d;
}

.badge-put {
  background: #fee2e2;
  color: #b91c1c;
}

/* ── Delta colouring ─────────────────────────────────────────────────────── */
.delta-high {
  color: var(--color-primary, #2563eb);
  font-weight: 600;
}

.delta-mid {
  color: var(--color-text, #334155);
}

.delta-low {
  color: var(--color-text-muted, #94a3b8);
}

/* ── Table footer ────────────────────────────────────────────────────────── */
.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.875rem;
  background: var(--color-surface-alt, #f8fafc);
  border-top: 1px solid var(--color-border, #e2e8f0);
  font-size: 0.8rem;
  color: var(--color-text-muted, #64748b);
}

.vix-badge {
  background: var(--color-primary-light, #dbeafe);
  color: var(--color-primary-dark, #1d4ed8);
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-size: 0.78rem;
}

/* ── Accessibility ───────────────────────────────────────────────────────── */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* ── Responsive: stack on narrow screens ─────────────────────────────────── */
@media (max-width: 640px) {
  .options-table,
  .options-table thead,
  .options-table tbody,
  .options-table th,
  .options-table td,
  .options-table tr {
    display: block;
  }

  .options-table thead {
    position: static;
  }

  .options-table thead tr {
    display: none;
  }

  .options-table tbody tr {
    margin-bottom: 0.75rem;
    border: 1px solid var(--color-border, #e2e8f0);
    border-radius: 0.375rem;
    overflow: hidden;
  }

  .options-table td {
    display: flex;
    justify-content: space-between;
    align-items: center;
    text-align: right;
    padding: 0.4rem 0.75rem;
    border-bottom: 1px solid var(--color-border-light, #f1f5f9);
  }

  .options-table td::before {
    content: attr(data-label);
    font-weight: 600;
    font-size: 0.75rem;
    color: var(--color-text-muted, #64748b);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    flex-shrink: 0;
    margin-right: 0.5rem;
    text-align: left;
  }

  .options-table td.col-ticker,
  .options-table td.col-expiry,
  .options-table td.col-type {
    text-align: right;
  }
}
</style>