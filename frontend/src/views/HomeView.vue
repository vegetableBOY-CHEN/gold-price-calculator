<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchPrices } from '@/api'
import type { GoldPriceItem, GoldPriceOverview, MarketGoldPrice } from '@/types'

const router = useRouter()
const prices = ref<GoldPriceOverview | null>(null)
const loading = ref(true)
const error = ref('')
const lastLoadedAt = ref<Date | null>(null)
const refreshing = ref(false)
let timer: number | undefined

const marketPrices = computed(() => [
  ...(prices.value?.international ?? []),
  ...(prices.value?.domestic_markets ?? []),
])

const liveCount = computed(() => marketPrices.value.filter((item) => item.status === 'live').length)
const brandRefreshText = computed(() => {
  const seconds = prices.value?.brand_refresh_interval_seconds ?? 28800
  if (seconds >= 3600) return `${Math.round(seconds / 3600)} 小时`
  return `${Math.round(seconds / 60)} 分钟`
})

onMounted(async () => {
  await load()
  const interval = Math.max((prices.value?.market_refresh_interval_seconds ?? 5) * 1000, 5000)
  timer = window.setInterval(load, interval)
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
})

async function load() {
  if (refreshing.value) return
  refreshing.value = true
  try {
    error.value = ''
    prices.value = mergeWithPreviousPrices(await fetchPrices(), prices.value)
    lastLoadedAt.value = new Date()
  } catch {
    error.value = '行情刷新失败，正在显示最近一次数据'
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function mergeWithPreviousPrices(next: GoldPriceOverview, previous: GoldPriceOverview | null) {
  if (!previous) return next

  const previousMarkets = [...previous.international, ...previous.domestic_markets]
  const keepPreviousValue = (item: MarketGoldPrice) => {
    if (item.price > 0 || item.status === 'live') return item
    const matched = previousMarkets.find((oldItem) => oldItem.market === item.market && oldItem.symbol === item.symbol)
    return matched && matched.price > 0
      ? { ...item, price: matched.price, source: matched.source, status: 'cached', update_time: matched.update_time }
      : item
  }

  return {
    ...next,
    international: next.international.map(keepPreviousValue),
    domestic_markets: next.domestic_markets.map(keepPreviousValue),
  }
}

function fmtPrice(price: number, digits = 2) {
  return price.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function fmtMarketUnit(item: MarketGoldPrice) {
  return `${item.currency}/${item.unit}`
}

function fmtMoney(price: number) {
  return `¥${fmtPrice(price)}/g`
}

function fmtChange(item: MarketGoldPrice) {
  if (item.change_percent == null && item.change == null) return '暂无涨跌'
  const pieces = []
  if (item.change != null) pieces.push(item.change > 0 ? `+${fmtPrice(item.change)}` : fmtPrice(item.change))
  if (item.change_percent != null) pieces.push(`${item.change_percent > 0 ? '+' : ''}${fmtPrice(item.change_percent)}%`)
  return pieces.join(' / ')
}

function fmtTime(iso?: string | null) {
  if (!iso) return '待更新'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false, timeZone: 'Asia/Shanghai' })
}

function priceClass(item: MarketGoldPrice) {
  return {
    up: (item.change ?? 0) > 0 || (item.change_percent ?? 0) > 0,
    down: (item.change ?? 0) < 0 || (item.change_percent ?? 0) < 0,
  }
}

function brandSpread(item: GoldPriceItem) {
  if (item.bar_price == null) return '暂无'
  return `+¥${fmtPrice(item.gold_price - item.bar_price)}/g`
}

function statusClass(item: MarketGoldPrice) {
  return item.status === 'live' ? 'live' : item.status === 'cached' ? 'cached' : 'fallback'
}

function statusText(item: MarketGoldPrice) {
  if (item.status === 'live') return '实时'
  if (item.status === 'cached') return '缓存'
  return '兜底'
}
</script>

<template>
  <div class="market-page">
    <header class="market-header">
      <div>
        <p class="eyebrow">实时金价大盘</p>
        <h1>国际、国内与品牌店铺金价</h1>
      </div>
      <div class="header-actions">
        <button class="btn" :disabled="loading || refreshing" @click="load">刷新</button>
        <button class="btn btn-primary" @click="router.push('/calculate')">去计算成本</button>
      </div>
    </header>

    <section class="status-strip" aria-label="行情状态">
      <div>
        <span>大盘刷新</span>
        <strong>{{ prices?.market_refresh_interval_seconds ?? 5 }} 秒</strong>
      </div>
      <div>
        <span>品牌价刷新</span>
        <strong>{{ brandRefreshText }}</strong>
      </div>
      <div>
        <span>实时源</span>
        <strong>{{ liveCount ? `${liveCount} 路 AllTick` : '本地兜底' }}</strong>
      </div>
      <div>
        <span>本次同步</span>
        <strong>{{ lastLoadedAt ? lastLoadedAt.toLocaleTimeString('zh-CN', { hour12: false }) : '加载中' }}</strong>
      </div>
    </section>

    <p v-if="error" class="notice">{{ error }}</p>

    <section class="market-grid" aria-label="国际国内大盘价格">
      <article v-for="item in marketPrices" :key="`${item.market}-${item.symbol}`" class="quote-card">
        <div class="quote-head">
          <div>
            <p class="quote-market">{{ item.market === 'international' ? '国际大盘' : '国内大盘' }}</p>
            <h2>{{ item.name }}</h2>
          </div>
          <span :class="['source-pill', statusClass(item)]">
            {{ statusText(item) }}
          </span>
        </div>
        <p :class="['quote-price', priceClass(item)]">
          {{ fmtPrice(item.price) }}
          <span>{{ fmtMarketUnit(item) }}</span>
        </p>
        <div class="quote-meta">
          <span>{{ item.exchange || 'AllTick' }} · {{ item.symbol }}</span>
          <strong :class="priceClass(item)">{{ fmtChange(item) }}</strong>
        </div>
        <p class="quote-time">更新 {{ fmtTime(item.update_time) }} · {{ item.source }}</p>
      </article>

      <article v-if="!marketPrices.length && !loading" class="empty-card">
        暂无大盘行情配置
      </article>
    </section>

    <section class="brand-section">
      <div class="section-title">
        <div>
          <p class="eyebrow">黄金店铺</p>
          <h2>饰品金与金条价格</h2>
        </div>
        <p>每 {{ brandRefreshText }} 更新一次</p>
      </div>

      <div class="brand-table-wrap">
        <table class="brand-table">
          <thead>
            <tr>
              <th>品牌</th>
              <th>饰品金</th>
              <th>金条价</th>
              <th>饰品溢价</th>
              <th>更新时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="brand in prices?.brands ?? []" :key="brand.brand">
              <td>
                <strong>{{ brand.brand_name }}</strong>
                <span>{{ brand.brand }}</span>
              </td>
              <td>{{ fmtMoney(brand.gold_price) }}</td>
              <td>{{ brand.bar_price != null ? fmtMoney(brand.bar_price) : '暂无' }}</td>
              <td>{{ brandSpread(brand) }}</td>
              <td>{{ fmtTime(brand.update_time) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.market-page { display: flex; flex-direction: column; gap: 1rem; }
.market-header { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-end; }
.eyebrow { color: var(--gold); font-size: 0.78rem; font-weight: 700; margin-bottom: 0.2rem; }
.market-header h1 { font-size: 1.55rem; line-height: 1.25; }
.header-actions { display: flex; gap: 0.6rem; flex-wrap: wrap; justify-content: flex-end; }
.status-strip { display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid var(--border); background: var(--surface); border-radius: 8px; overflow: hidden; }
.status-strip div { padding: 0.8rem 1rem; border-right: 1px solid var(--border); }
.status-strip div:last-child { border-right: 0; }
.status-strip span, .section-title p, .quote-time, .quote-market, .brand-table span { color: var(--text-muted); font-size: 0.78rem; }
.status-strip strong { display: block; margin-top: 0.2rem; font-size: 0.95rem; }
.notice { color: #8a5a00; background: var(--warn-bg); border: 1px solid #f4dc9a; border-radius: 6px; padding: 0.6rem 0.8rem; font-size: 0.86rem; }
.market-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.quote-card, .empty-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.1rem; }
.quote-head, .quote-meta, .section-title { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }
.quote-head h2, .section-title h2 { font-size: 1rem; }
.source-pill { border: 1px solid var(--border); border-radius: 999px; padding: 0.18rem 0.55rem; font-size: 0.75rem; white-space: nowrap; }
.source-pill.live { color: #187a45; background: #e9f7ef; border-color: #bee5cc; }
.source-pill.fallback { color: #76520a; background: var(--warn-bg); border-color: #f4dc9a; }
.source-pill.cached { color: #315f89; background: #edf5fb; border-color: #bfd8eb; }
.quote-price { font-size: 2rem; font-weight: 750; line-height: 1.1; margin: 1.1rem 0 0.6rem; }
.quote-price span { color: var(--text-muted); font-size: 0.85rem; font-weight: 500; }
.quote-meta { align-items: center; color: var(--text-muted); font-size: 0.82rem; }
.quote-meta strong, .up { color: #c0392b; }
.quote-meta strong.down, .down { color: #1f8f4d; }
.quote-time { margin-top: 0.65rem; }
.brand-section { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.1rem; }
.section-title { align-items: flex-end; margin-bottom: 1rem; }
.brand-table-wrap { overflow-x: auto; }
.brand-table { width: 100%; border-collapse: collapse; min-width: 720px; font-size: 0.88rem; }
.brand-table th { color: var(--text-muted); font-weight: 600; text-align: left; padding: 0.55rem 0.35rem; border-bottom: 1px solid var(--border); }
.brand-table td { padding: 0.7rem 0.35rem; border-bottom: 1px solid var(--border); }
.brand-table tr:last-child td { border-bottom: 0; }
.brand-table td:first-child strong, .brand-table td:first-child span { display: block; }
.empty-card { color: var(--text-muted); }
@media (max-width: 760px) {
  .market-header, .section-title { flex-direction: column; align-items: stretch; }
  .header-actions { justify-content: stretch; }
  .header-actions .btn { flex: 1; }
  .status-strip, .market-grid { grid-template-columns: 1fr; }
  .status-strip div { border-right: 0; border-bottom: 1px solid var(--border); }
  .status-strip div:last-child { border-bottom: 0; }
}
</style>
