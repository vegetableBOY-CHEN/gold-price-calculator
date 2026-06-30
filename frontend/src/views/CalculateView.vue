<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { fetchPrices, fetchRules, calculateCost } from '@/api'
import type { CostCalculationResult, ExchangeRule, GoldPriceItem } from '@/types'

const brands = ref<GoldPriceItem[]>([])
const rules = ref<ExchangeRule[]>([])
const loading = ref(false)
const result = ref<CostCalculationResult | null>(null)
const error = ref('')

const brand = ref('')
const newWeight = ref<number | null>(10)
const newPrice = ref<number | null>(null)
const laborFee = ref<number | null>(null)
const oldWeight = ref<number | null>(0)
const oldBrand = ref('')
const oldIsBar = ref(false)
const recyclePrice = ref<number | null>(null)
const ruleId = ref<number | null>(null)
const useCustomRule = ref(false)

const customRule = ref({
  support_bar: true,
  support_other_brand: true,
  support_old_jewelry: true,
  need_extra_gold: false,
  extra_rate: 0,
  loss_type: 'fixed' as const,
  loss_value: 0,
  labor_type: 'perGram' as const,
  labor_value: 30,
  recycle_price_type: 'recycle' as const,
})

const brandRules = computed(() => rules.value.filter((r) => r.brand === brand.value))

onMounted(async () => {
  const [priceData, ruleData] = await Promise.all([fetchPrices(), fetchRules()])
  brands.value = priceData.brands
  rules.value = ruleData
  if (brands.value.length) {
    brand.value = brands.value[0].brand
    newPrice.value = brands.value[0].gold_price
  }
})

watch(brand, (id) => {
  const b = brands.value.find((x) => x.brand === id)
  if (b) newPrice.value = b.gold_price
  const matched = brandRules.value[0]
  if (matched) ruleId.value = matched.id ?? null
})

watch(ruleId, (id) => {
  if (!id || useCustomRule.value) return
  const rule = rules.value.find((r) => r.id === id)
  if (!rule) return
  customRule.value = {
    support_bar: rule.support_bar,
    support_other_brand: rule.support_other_brand,
    support_old_jewelry: rule.support_old_jewelry,
    need_extra_gold: rule.need_extra_gold,
    extra_rate: rule.extra_rate,
    loss_type: rule.loss_type,
    loss_value: rule.loss_value,
    labor_type: rule.labor_type,
    labor_value: rule.labor_value,
    recycle_price_type: rule.recycle_price_type,
  }
})

function fmt(n: number) {
  return `¥${n.toFixed(2)}`
}

function formatValue(item: { label: string; value: number }) {
  if (['旧金重量', '可抵扣重量'].includes(item.label)) return `${item.value}g`
  if (item.label === '损耗') return `${item.value}g`
  if (item.label === '旧金抵扣') return `- ${fmt(Math.abs(item.value))}`
  return fmt(item.value)
}

async function submit() {
  if (!brand.value || !newWeight.value || !newPrice.value) {
    error.value = '请填写品牌、重量和金价'
    return
  }
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await calculateCost({
      purchase: {
        brand: brand.value,
        new_weight: newWeight.value,
        new_price: newPrice.value,
        labor_fee: laborFee.value,
        old_weight: oldWeight.value ?? 0,
        old_brand: oldBrand.value || null,
        old_is_bar: oldIsBar.value,
        recycle_price: recyclePrice.value,
      },
      rule_id: useCustomRule.value ? null : ruleId.value,
      exchange_rule: useCustomRule.value ? customRule.value : null,
    })
  } catch {
    error.value = '计算失败，请检查输入或置换规则'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="page-title">成本计算</h1>

    <div class="calc-layout">
      <div class="calc-form card">
        <h2 class="section-label">购买信息</h2>

        <div class="form-group" style="margin-bottom: 1rem">
          <label>新金品牌</label>
          <select v-model="brand">
            <option v-for="b in brands" :key="b.brand" :value="b.brand">{{ b.brand_name }}</option>
          </select>
        </div>

        <div class="form-row" style="margin-bottom: 1rem">
          <div class="form-group">
            <label>新金重量 (g)</label>
            <input v-model.number="newWeight" type="number" step="0.01" min="0.01" />
          </div>
          <div class="form-group">
            <label>金价 (元/g)</label>
            <input v-model.number="newPrice" type="number" step="0.01" min="0.01" />
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 1rem">
          <label>工费 (元，留空按规则计算)</label>
          <input v-model.number="laborFee" type="number" step="0.01" min="0" placeholder="自动" />
        </div>

        <h2 class="section-label">旧金信息</h2>

        <div class="form-row" style="margin-bottom: 1rem">
          <div class="form-group">
            <label>旧金重量 (g)</label>
            <input v-model.number="oldWeight" type="number" step="0.01" min="0" />
          </div>
          <div class="form-group">
            <label>旧金品牌</label>
            <input v-model="oldBrand" type="text" placeholder="可选" />
          </div>
        </div>

        <div class="checkbox-row" style="margin-bottom: 1rem">
          <label><input v-model="oldIsBar" type="checkbox" /> 金条</label>
        </div>

        <div class="form-group" style="margin-bottom: 1rem">
          <label>回收价 (元/g，留空自动推算)</label>
          <input v-model.number="recyclePrice" type="number" step="0.01" min="0" placeholder="自动" />
        </div>

        <h2 class="section-label">置换规则</h2>

        <div class="form-group" style="margin-bottom: 0.75rem">
          <label>规则模板</label>
          <select v-model="ruleId" :disabled="useCustomRule">
            <option :value="null">默认规则</option>
            <option v-for="r in brandRules" :key="r.id" :value="r.id">{{ r.name }}</option>
          </select>
        </div>

        <label class="custom-toggle">
          <input v-model="useCustomRule" type="checkbox" /> 自定义规则
        </label>

        <div v-if="useCustomRule" class="rule-panel">
          <div class="checkbox-row">
            <label><input v-model="customRule.support_bar" type="checkbox" /> 支持金条</label>
            <label><input v-model="customRule.support_other_brand" type="checkbox" /> 跨品牌</label>
            <label><input v-model="customRule.support_old_jewelry" type="checkbox" /> 旧饰品</label>
            <label><input v-model="customRule.need_extra_gold" type="checkbox" /> 要求增金</label>
          </div>
          <div class="form-row" style="margin-top: 0.75rem">
            <div class="form-group">
              <label>增金比例 (%)</label>
              <input v-model.number="customRule.extra_rate" type="number" min="0" />
            </div>
            <div class="form-group">
              <label>损耗类型</label>
              <select v-model="customRule.loss_type">
                <option value="fixed">固定克数</option>
                <option value="percentage">百分比</option>
              </select>
            </div>
          </div>
          <div class="form-row" style="margin-top: 0.75rem">
            <div class="form-group">
              <label>损耗值</label>
              <input v-model.number="customRule.loss_value" type="number" min="0" step="0.01" />
            </div>
            <div class="form-group">
              <label>工费类型</label>
              <select v-model="customRule.labor_type">
                <option value="fixed">固定</option>
                <option value="perGram">按克</option>
              </select>
            </div>
          </div>
          <div class="form-row" style="margin-top: 0.75rem">
            <div class="form-group">
              <label>工费值</label>
              <input v-model.number="customRule.labor_value" type="number" min="0" />
            </div>
            <div class="form-group">
              <label>回收计价</label>
              <select v-model="customRule.recycle_price_type">
                <option value="recycle">回收价</option>
                <option value="jewelry">饰品价</option>
              </select>
            </div>
          </div>
        </div>

        <button class="btn btn-primary calc-btn" :disabled="loading" @click="submit">
          {{ loading ? '计算中…' : '开始计算' }}
        </button>
        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <div class="calc-result card">
        <h2 class="section-label">计算结果</h2>

        <template v-if="result">
          <div class="highlight">
            <p class="text-muted">最终花费</p>
            <p class="final-cost">{{ fmt(result.final_cost) }}</p>
            <p class="per-gram">克均价 <strong>{{ fmt(result.price_per_gram) }}/g</strong></p>
          </div>

          <ul class="breakdown">
            <li v-for="(item, i) in result.breakdown" :key="i">
              <span>{{ item.label }}<small v-if="item.detail"> · {{ item.detail }}</small></span>
              <span>{{ formatValue(item) }}</span>
            </li>
          </ul>

          <ul v-if="result.warnings.length" class="warnings">
            <li v-for="(w, i) in result.warnings" :key="i">{{ w }}</li>
          </ul>
        </template>

        <p v-else class="text-muted empty">填写信息后点击计算</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.calc-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  align-items: start;
}

.section-label {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.custom-toggle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
  cursor: pointer;
}

.rule-panel {
  padding: 0.75rem;
  background: var(--bg);
  border-radius: 6px;
  margin-bottom: 1rem;
}

.calc-btn {
  width: 100%;
  margin-top: 0.5rem;
}

.error {
  color: var(--danger);
  font-size: 0.85rem;
  margin-top: 0.75rem;
  text-align: center;
}

.highlight {
  text-align: center;
  padding: 1rem 0 1.25rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1rem;
}

.final-cost {
  font-size: 2rem;
  font-weight: 600;
}

.per-gram {
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.per-gram strong {
  color: var(--gold);
}

.breakdown {
  list-style: none;
}

.breakdown li {
  display: flex;
  justify-content: space-between;
  padding: 0.45rem 0;
  font-size: 0.875rem;
  border-bottom: 1px solid var(--border);
}

.breakdown small {
  color: var(--text-muted);
}

.warnings {
  list-style: none;
  margin-top: 1rem;
}

.warnings li {
  font-size: 0.8rem;
  color: #856404;
  background: var(--warn-bg);
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  margin-bottom: 0.35rem;
}

.empty {
  text-align: center;
  padding: 3rem 0;
}

@media (max-width: 768px) {
  .calc-layout {
    grid-template-columns: 1fr;
  }
}
</style>
