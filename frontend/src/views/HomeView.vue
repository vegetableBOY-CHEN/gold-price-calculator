<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchPrices, updatePrices } from '@/api'
import type { GoldPriceOverview } from '@/types'

const router = useRouter()
const prices = ref<GoldPriceOverview | null>(null)
const editing = ref(false)
const domesticInput = ref(0)
const brandInputs = ref<{ brand: string; brand_name: string; gold_price: number; bar_price: number | null }[]>([])
const saving = ref(false)

onMounted(load)

async function load() {
  prices.value = await fetchPrices()
  syncInputs()
}

function syncInputs() {
  if (!prices.value) return
  domesticInput.value = prices.value.domestic.price
  brandInputs.value = prices.value.brands.map((b) => ({
    brand: b.brand,
    brand_name: b.brand_name,
    gold_price: b.gold_price,
    bar_price: b.bar_price ?? null,
  }))
}

function formatTime(iso?: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

async function savePrices() {
  saving.value = true
  try {
    prices.value = await updatePrices({
      domestic_price: domesticInput.value,
      brands: brandInputs.value,
    })
    editing.value = false
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="page-title">今日金价</h1>

    <section v-if="prices" class="card domestic-card">
      <div class="domestic-row">
        <div>
          <p class="text-muted">国内大盘金价</p>
          <template v-if="!editing">
            <p class="domestic-price">¥{{ prices.domestic.price }}<span>/g</span></p>
          </template>
          <input v-else v-model.number="domesticInput" type="number" step="0.01" class="inline-input" />
        </div>
        <p class="text-muted update-time">更新 {{ formatTime(prices.domestic.update_time) }}</p>
      </div>
    </section>

    <section v-if="prices" class="card brand-card">
      <div class="section-head">
        <h2>品牌金价</h2>
        <button v-if="!editing" class="btn btn-sm" @click="editing = true; syncInputs()">编辑</button>
        <div v-else class="edit-actions">
          <button class="btn btn-sm" @click="editing = false; syncInputs()">取消</button>
          <button class="btn btn-sm btn-primary" :disabled="saving" @click="savePrices">保存</button>
        </div>
      </div>

      <table class="price-table">
        <thead>
          <tr>
            <th>品牌</th>
            <th>饰品金价</th>
            <th>金条价格</th>
            <th>更新时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(b, i) in editing ? brandInputs : prices.brands" :key="b.brand">
            <td>{{ b.brand_name }}</td>
            <td>
              <template v-if="!editing">¥{{ b.gold_price }}/g</template>
              <input v-else v-model.number="brandInputs[i].gold_price" type="number" step="0.01" class="table-input" />
            </td>
            <td>
              <template v-if="!editing">{{ b.bar_price != null ? `¥${b.bar_price}/g` : '—' }}</template>
              <input v-else v-model.number="brandInputs[i].bar_price" type="number" step="0.01" class="table-input" placeholder="—" />
            </td>
            <td class="text-muted">{{ editing ? '—' : formatTime(prices.brands[i].update_time) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <div class="action-row">
      <button class="btn btn-primary btn-lg" @click="router.push('/calculate')">开始计算</button>
    </div>
  </div>
</template>

<style scoped>
.domestic-card {
  margin-bottom: 1rem;
}

.domestic-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.domestic-price {
  font-size: 2rem;
  font-weight: 600;
  margin-top: 0.25rem;
}

.domestic-price span {
  font-size: 1rem;
  font-weight: 400;
  color: var(--text-muted);
}

.inline-input {
  font-size: 1.5rem;
  width: 120px;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  margin-top: 0.25rem;
}

.update-time {
  font-size: 0.8rem;
}

.brand-card {
  margin-bottom: 2rem;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-head h2 {
  font-size: 0.95rem;
  font-weight: 600;
}

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
}

.edit-actions {
  display: flex;
  gap: 0.5rem;
}

.price-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.price-table th {
  text-align: left;
  font-weight: 500;
  color: var(--text-muted);
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}

.price-table td {
  padding: 0.65rem 0;
  border-bottom: 1px solid var(--border);
}

.table-input {
  width: 90px;
  padding: 0.3rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 4px;
}

.action-row {
  text-align: center;
}

.btn-lg {
  padding: 0.75rem 2.5rem;
  font-size: 0.95rem;
}
</style>
