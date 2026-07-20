<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { calculateCost, fetchPrices, fetchRules } from '@/api'
import type {
  CostCalculationRequest,
  CostCalculationResult,
  ExchangeRule,
  ExchangeRuleInline,
  GoldPriceItem,
} from '@/types'

interface CalculationScenario {
  id: number
  name: string
  brand: string
  newWeight: number | null
  newPrice: number | null
  laborFee: number | null
  oldWeight: number | null
  oldPurchaseCost: number | null
  oldBrand: string
  oldIsBar: boolean
  recyclePrice: number | null
  ruleId: number | null
  useCustomRule: boolean
  customRule: ExchangeRuleInline
  result: CostCalculationResult | null
  error: string
  loading: boolean
}

const brands = ref<GoldPriceItem[]>([])
const rules = ref<ExchangeRule[]>([])
const scenarios = ref<CalculationScenario[]>([])
const activeId = ref(1)
let nextId = 1

const activeScenario = computed(() => scenarios.value.find((item) => item.id === activeId.value)!)
const brandRules = computed(() =>
  rules.value.filter((rule) => rule.brand === activeScenario.value?.brand),
)
const calculatedScenarios = computed(() => scenarios.value.filter((item) => item.result))
const bestScenarioId = computed(() => {
  if (!calculatedScenarios.value.length) return null
  return calculatedScenarios.value.reduce((best, item) =>
    item.result!.price_per_gram < best.result!.price_per_gram ? item : best,
  ).id
})
const calculatingAll = computed(() => scenarios.value.some((item) => item.loading))

function defaultRule(): ExchangeRuleInline {
  return {
    support_bar: true,
    support_other_brand: true,
    support_old_jewelry: true,
    need_extra_gold: false,
    extra_rate: 0,
    loss_type: 'fixed',
    loss_value: 0,
    labor_type: 'perGram',
    labor_value: 30,
    recycle_price_type: 'recycle',
  }
}

function createScenario(source?: CalculationScenario): CalculationScenario {
  const id = nextId++
  if (source) {
    return {
      ...source,
      id,
      name: `方案 ${id}`,
      customRule: { ...source.customRule },
      result: null,
      error: '',
      loading: false,
    }
  }
  const firstBrand = brands.value[0]
  return {
    id,
    name: `方案 ${id}`,
    brand: firstBrand?.brand ?? '',
    newWeight: 10,
    newPrice: firstBrand?.gold_price ?? null,
    laborFee: null,
    oldWeight: 0,
    oldPurchaseCost: 0,
    oldBrand: '',
    oldIsBar: false,
    recyclePrice: null,
    ruleId: null,
    useCustomRule: false,
    customRule: defaultRule(),
    result: null,
    error: '',
    loading: false,
  }
}

onMounted(async () => {
  try {
    const [priceData, ruleData] = await Promise.all([fetchPrices(), fetchRules()])
    brands.value = priceData.brands
    rules.value = ruleData
    scenarios.value = [createScenario()]
    activeId.value = scenarios.value[0].id
    syncBrandDefaults(scenarios.value[0])
  } catch {
    scenarios.value = [createScenario()]
    activeId.value = scenarios.value[0].id
    scenarios.value[0].error = '基础数据加载失败，请刷新页面重试'
  }
})

function syncBrandDefaults(scenario: CalculationScenario) {
  const selectedBrand = brands.value.find((item) => item.brand === scenario.brand)
  if (selectedBrand) scenario.newPrice = selectedBrand.gold_price
  const matchedRule = rules.value.find((rule) => rule.brand === scenario.brand)
  scenario.ruleId = matchedRule?.id ?? null
  if (matchedRule) applyRule(scenario, matchedRule)
  scenario.result = null
}

function syncRule(scenario: CalculationScenario) {
  if (!scenario.ruleId || scenario.useCustomRule) return
  const rule = rules.value.find((item) => item.id === scenario.ruleId)
  if (rule) applyRule(scenario, rule)
  scenario.result = null
}

function applyRule(scenario: CalculationScenario, rule: ExchangeRule) {
  scenario.customRule = {
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
}

function addScenario(source?: CalculationScenario) {
  const scenario = createScenario(source)
  scenarios.value.push(scenario)
  activeId.value = scenario.id
  if (!source) syncBrandDefaults(scenario)
}

function removeScenario(id: number) {
  if (scenarios.value.length === 1) return
  const index = scenarios.value.findIndex((item) => item.id === id)
  scenarios.value.splice(index, 1)
  if (activeId.value === id) {
    activeId.value = scenarios.value[Math.min(index, scenarios.value.length - 1)].id
  }
}

function fmt(n: number) {
  return `¥${n.toFixed(2)}`
}

function formatValue(item: { label: string; value: number }) {
  if (['旧金重量', '可抵扣重量', '损耗'].includes(item.label)) return `${item.value}g`
  if (item.label === '旧金抵扣') return `- ${fmt(Math.abs(item.value))}`
  if (item.label === '置换节省') return formatSavings(item.value)
  return fmt(item.value)
}

function formatSavings(n: number) {
  if (n > 0) return `省 ${fmt(n)}`
  if (n < 0) return `多花 ${fmt(Math.abs(n))}`
  return '持平'
}

function buildRequest(scenario: CalculationScenario): CostCalculationRequest | null {
  if (!scenario.brand || !scenario.newWeight || !scenario.newPrice) {
    scenario.error = '请填写品牌、重量和金价'
    return null
  }
  return {
    purchase: {
      brand: scenario.brand,
      new_weight: scenario.newWeight,
      new_price: scenario.newPrice,
      labor_fee: scenario.laborFee,
      old_weight: scenario.oldWeight ?? 0,
      old_purchase_cost: scenario.oldPurchaseCost ?? 0,
      old_brand: scenario.oldBrand || null,
      old_is_bar: scenario.oldIsBar,
      recycle_price: scenario.recyclePrice,
    },
    rule_id: scenario.useCustomRule ? null : scenario.ruleId,
    exchange_rule: scenario.useCustomRule ? scenario.customRule : null,
  }
}

async function calculateScenario(scenario: CalculationScenario) {
  scenario.error = ''
  const request = buildRequest(scenario)
  if (!request) return
  scenario.loading = true
  try {
    scenario.result = await calculateCost(request)
  } catch {
    scenario.error = '计算失败，请检查输入或置换规则'
  } finally {
    scenario.loading = false
  }
}

async function calculateAll() {
  await Promise.all(scenarios.value.map(calculateScenario))
}
</script>

<template>
  <div>
    <div class="page-heading">
      <div>
        <h1 class="page-title">成本计算</h1>
        <p class="text-muted">创建多个方案，对比真实克均价并找出更划算的选择。</p>
      </div>
      <button class="btn" @click="addScenario()">+ 新增方案</button>
    </div>

    <div v-if="activeScenario" class="scenario-bar">
      <button
        v-for="scenario in scenarios"
        :key="scenario.id"
        class="scenario-tab"
        :class="{ active: scenario.id === activeId }"
        @click="activeId = scenario.id"
      >
        <span>{{ scenario.name }}</span>
        <small v-if="scenario.result">{{ fmt(scenario.result.price_per_gram) }}/g</small>
      </button>
    </div>

    <div v-if="activeScenario" class="scenario-actions card">
      <input v-model.trim="activeScenario.name" maxlength="20" aria-label="方案名称" />
      <button class="btn compact" @click="addScenario(activeScenario)">复制方案</button>
      <button
        class="btn btn-danger compact"
        :disabled="scenarios.length === 1"
        @click="removeScenario(activeScenario.id)"
      >删除方案</button>
    </div>

    <div v-if="activeScenario" class="calc-layout">
      <div class="calc-form card">
        <h2 class="section-label">购买信息</h2>
        <div class="form-group field-space">
          <label>新金品牌</label>
          <select v-model="activeScenario.brand" @change="syncBrandDefaults(activeScenario)">
            <option v-for="b in brands" :key="b.brand" :value="b.brand">{{ b.brand_name }}</option>
          </select>
        </div>
        <div class="form-row field-space">
          <div class="form-group"><label>新金重量 (g)</label><input v-model.number="activeScenario.newWeight" type="number" step="0.01" min="0.01" /></div>
          <div class="form-group"><label>金价 (元/g)</label><input v-model.number="activeScenario.newPrice" type="number" step="0.01" min="0.01" /></div>
        </div>
        <div class="form-group field-space">
          <label>工费 (元，留空按规则计算)</label><input v-model.number="activeScenario.laborFee" type="number" step="0.01" min="0" placeholder="自动" />
        </div>

        <h2 class="section-label">旧金信息</h2>
        <div class="form-row field-space">
          <div class="form-group"><label>旧金重量 (g)</label><input v-model.number="activeScenario.oldWeight" type="number" step="0.01" min="0" /></div>
          <div class="form-group"><label>旧金购买成本 (元)</label><input v-model.number="activeScenario.oldPurchaseCost" type="number" step="0.01" min="0" /></div>
        </div>
        <div class="form-row field-space">
          <div class="form-group"><label>旧金品牌</label><input v-model="activeScenario.oldBrand" type="text" placeholder="可选" /></div>
        </div>
        <div class="checkbox-row field-space"><label><input v-model="activeScenario.oldIsBar" type="checkbox" /> 金条</label></div>
        <div class="form-group field-space">
          <label>回收价 (元/g，留空自动推算)</label><input v-model.number="activeScenario.recyclePrice" type="number" step="0.01" min="0" placeholder="自动" />
        </div>

        <h2 class="section-label">置换规则</h2>
        <div class="form-group rule-select">
          <label>规则模板</label>
          <select v-model="activeScenario.ruleId" :disabled="activeScenario.useCustomRule" @change="syncRule(activeScenario)">
            <option :value="null">默认规则</option>
            <option v-for="r in brandRules" :key="r.id" :value="r.id">{{ r.name }}</option>
          </select>
        </div>
        <label class="custom-toggle"><input v-model="activeScenario.useCustomRule" type="checkbox" /> 自定义规则</label>
        <div v-if="activeScenario.useCustomRule" class="rule-panel">
          <div class="checkbox-row">
            <label><input v-model="activeScenario.customRule.support_bar" type="checkbox" /> 支持金条</label>
            <label><input v-model="activeScenario.customRule.support_other_brand" type="checkbox" /> 跨品牌</label>
            <label><input v-model="activeScenario.customRule.support_old_jewelry" type="checkbox" /> 旧饰品</label>
            <label><input v-model="activeScenario.customRule.need_extra_gold" type="checkbox" /> 要求增金</label>
          </div>
          <div class="form-row rule-row">
            <div class="form-group"><label>增金比例 (%)</label><input v-model.number="activeScenario.customRule.extra_rate" type="number" min="0" /></div>
            <div class="form-group"><label>损耗类型</label><select v-model="activeScenario.customRule.loss_type"><option value="fixed">固定克数</option><option value="percentage">百分比</option></select></div>
          </div>
          <div class="form-row rule-row">
            <div class="form-group"><label>损耗值</label><input v-model.number="activeScenario.customRule.loss_value" type="number" min="0" step="0.01" /></div>
            <div class="form-group"><label>工费类型</label><select v-model="activeScenario.customRule.labor_type"><option value="fixed">固定</option><option value="perGram">按克</option></select></div>
          </div>
          <div class="form-row rule-row">
            <div class="form-group"><label>工费值</label><input v-model.number="activeScenario.customRule.labor_value" type="number" min="0" /></div>
            <div class="form-group"><label>回收计价</label><select v-model="activeScenario.customRule.recycle_price_type"><option value="recycle">回收价</option><option value="jewelry">饰品价</option></select></div>
          </div>
        </div>
        <button class="btn btn-primary calc-btn" :disabled="activeScenario.loading" @click="calculateScenario(activeScenario)">
          {{ activeScenario.loading ? '计算中…' : `计算「${activeScenario.name}」` }}
        </button>
        <p v-if="activeScenario.error" class="error">{{ activeScenario.error }}</p>
      </div>

      <div class="calc-result card">
        <h2 class="section-label">{{ activeScenario.name }} · 计算结果</h2>
        <template v-if="activeScenario.result">
          <div class="highlight">
            <span v-if="bestScenarioId === activeScenario.id && calculatedScenarios.length > 1" class="best-badge">当前最优</span>
            <p class="text-muted">需补差价</p>
            <p class="final-cost">{{ fmt(activeScenario.result.final_cost) }}</p>
            <p class="per-gram">真实克均价 <strong>{{ fmt(activeScenario.result.price_per_gram) }}/g</strong><small>* 不含工费</small></p>
          </div>
          <div class="result-summary">
            <div><span>真实成本</span><strong>{{ fmt(activeScenario.result.actual_cost) }}</strong></div>
            <div><span>直接购买</span><strong>{{ fmt(activeScenario.result.direct_purchase_cost) }}</strong></div>
            <div :class="{ saved: activeScenario.result.savings_amount > 0, extra: activeScenario.result.savings_amount < 0 }"><span>置换结果</span><strong>{{ formatSavings(activeScenario.result.savings_amount) }}</strong></div>
          </div>
          <ul class="breakdown">
            <li v-for="(item, i) in activeScenario.result.breakdown" :key="i"><span>{{ item.label }}<small v-if="item.detail"> · {{ item.detail }}</small></span><span>{{ formatValue(item) }}</span></li>
          </ul>
          <ul v-if="activeScenario.result.warnings.length" class="warnings"><li v-for="(warning, i) in activeScenario.result.warnings" :key="i">{{ warning }}</li></ul>
        </template>
        <p v-else class="text-muted empty">填写信息后计算当前方案，或在下方计算全部方案。</p>
      </div>
    </div>

    <section v-if="scenarios.length > 1" class="comparison card">
      <div class="comparison-heading">
        <div><h2>方案对比</h2><p class="text-muted">以不含工费的真实克均价最低作为最优方案。</p></div>
        <button class="btn btn-primary" :disabled="calculatingAll" @click="calculateAll">{{ calculatingAll ? '计算中…' : '计算全部方案' }}</button>
      </div>
      <div class="comparison-grid">
        <article v-for="scenario in scenarios" :key="scenario.id" :class="['comparison-item', { best: scenario.id === bestScenarioId }]" @click="activeId = scenario.id">
          <div class="comparison-name"><strong>{{ scenario.name }}</strong><span v-if="scenario.id === bestScenarioId" class="best-badge">最优</span></div>
          <template v-if="scenario.result">
            <p class="comparison-price">{{ fmt(scenario.result.price_per_gram) }}<small>/g</small></p>
            <dl><div><dt>真实成本</dt><dd>{{ fmt(scenario.result.actual_cost) }}</dd></div><div><dt>需补差价</dt><dd>{{ fmt(scenario.result.final_cost) }}</dd></div><div><dt>置换结果</dt><dd>{{ formatSavings(scenario.result.savings_amount) }}</dd></div></dl>
          </template>
          <p v-else class="text-muted uncalculated">{{ scenario.error || '尚未计算' }}</p>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page-heading,.comparison-heading,.scenario-actions,.comparison-name{display:flex;align-items:center;justify-content:space-between;gap:1rem}.page-heading{margin-bottom:1rem}.page-heading .page-title{margin-bottom:.15rem}.scenario-bar{display:flex;gap:.5rem;overflow-x:auto;margin-bottom:.75rem;padding-bottom:.15rem}.scenario-tab{min-width:120px;padding:.65rem .9rem;border:1px solid var(--border);border-radius:7px;background:var(--surface);text-align:left}.scenario-tab span,.scenario-tab small{display:block}.scenario-tab small{color:var(--text-muted);font-size:.72rem}.scenario-tab.active{border-color:var(--gold);box-shadow:inset 0 -2px var(--gold)}.scenario-actions{justify-content:flex-start;padding:.75rem;margin-bottom:1rem}.scenario-actions input{min-width:0;width:220px;padding:.5rem .65rem;border:1px solid var(--border);border-radius:6px;font-weight:600}.compact{padding:.45rem .75rem;font-size:.82rem}.calc-layout{display:grid;grid-template-columns:1fr 1fr;gap:1rem;align-items:start}.section-label{font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted);margin-bottom:1rem}.field-space{margin-bottom:1rem}.rule-select{margin-bottom:.75rem}.custom-toggle{display:flex;align-items:center;gap:.4rem;font-size:.875rem;margin-bottom:.75rem;cursor:pointer}.rule-panel{padding:.75rem;background:var(--bg);border-radius:6px;margin-bottom:1rem}.rule-row{margin-top:.75rem}.calc-btn{width:100%;margin-top:.5rem}.error{color:var(--danger);font-size:.85rem;margin-top:.75rem;text-align:center}.highlight{text-align:center;padding:1rem 0 1.25rem;border-bottom:1px solid var(--border);margin-bottom:1rem}.best-badge{display:inline-block;padding:.15rem .45rem;border-radius:999px;background:#fff4cc;color:#8a6500;font-size:.7rem;font-weight:700}.final-cost{font-size:2rem;font-weight:600}.per-gram{font-size:.9rem;margin-top:.25rem}.per-gram strong{color:var(--gold)}.per-gram small{color:var(--text-muted);margin-left:.35rem}.result-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-bottom:1rem}.result-summary>div{padding:.75rem;border:1px solid var(--border);border-radius:6px;background:var(--bg)}.result-summary span{display:block;color:var(--text-muted);font-size:.75rem;margin-bottom:.35rem}.result-summary strong{display:block;font-size:1rem}.result-summary .saved strong{color:#1f8f4d}.result-summary .extra strong{color:var(--danger)}.breakdown{list-style:none}.breakdown li{display:flex;justify-content:space-between;padding:.45rem 0;font-size:.875rem;border-bottom:1px solid var(--border)}.breakdown small{color:var(--text-muted)}.warnings{list-style:none;margin-top:1rem}.warnings li{font-size:.8rem;color:#856404;background:var(--warn-bg);padding:.5rem .75rem;border-radius:4px;margin-bottom:.35rem}.empty{text-align:center;padding:3rem 0}.comparison{margin-top:1rem}.comparison-heading{margin-bottom:1rem}.comparison-heading h2{font-size:1rem}.comparison-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.75rem}.comparison-item{padding:1rem;border:1px solid var(--border);border-radius:7px;cursor:pointer}.comparison-item:hover{border-color:#ccc}.comparison-item.best{border-color:var(--gold);background:#fffdf5}.comparison-price{font-size:1.35rem;font-weight:700;color:var(--gold);margin:.75rem 0}.comparison-price small{font-size:.75rem}.comparison-item dl>div{display:flex;justify-content:space-between;font-size:.78rem;margin-top:.35rem}.comparison-item dt{color:var(--text-muted)}.comparison-item dd{font-weight:600}.uncalculated{padding:1.5rem 0;text-align:center}
@media(max-width:768px){.calc-layout{grid-template-columns:1fr}.result-summary{grid-template-columns:1fr}.comparison-heading{align-items:flex-start;flex-direction:column}.comparison-heading .btn{width:100%}}
@media(max-width:520px){.page-heading{align-items:flex-start}.scenario-actions{flex-wrap:wrap}.scenario-actions input{width:100%}}
</style>
