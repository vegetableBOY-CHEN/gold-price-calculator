<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import axios from 'axios'
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
  laborFeeType: 'perGram' | 'perItem'
  laborFee: number | null
  useOldGold: boolean
  oldGoldType: 'jewelry' | 'bar'
  oldWeight: number | null
  oldPurchaseCost: number | null
  oldBrand: string
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
const shareStatus = ref('')
const readyToPersist = ref(false)
let nextId = 1

const STORAGE_KEY = 'gold-price-calculator:scenarios:v1'
const SHARE_QUERY_KEY = 'plans'

const activeScenario = computed(() => scenarios.value.find((item) => item.id === activeId.value)!)
const brandRules = computed(() =>
  rules.value.filter((rule) => rule.brand === activeScenario.value?.brand),
)
const selectedTemplateRule = computed(() => {
  const scenario = activeScenario.value
  if (!scenario || scenario.useCustomRule || !scenario.ruleId) return null
  return rules.value.find((rule) => rule.id === scenario.ruleId) ?? null
})
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
    loss_type: 'percentage',
    loss_value: 0,
    labor_type: 'fixed',
    labor_value: 0,
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
    laborFeeType: 'perGram',
    laborFee: 0,
    useOldGold: false,
    oldGoldType: 'jewelry',
    oldWeight: 0,
    oldPurchaseCost: 0,
    oldBrand: '',
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
    restoreScenarios()
  } catch {
    restoreScenarios()
    scenarios.value[0].error = '基础数据加载失败，请刷新页面重试'
  } finally {
    readyToPersist.value = true
  }
})

watch(
  [scenarios, activeId],
  () => {
    if (!readyToPersist.value || !scenarios.value.length) return
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sharePayload()))
    } catch {
      // 浏览器禁用本地存储时仍允许正常计算。
    }
  },
  { deep: true },
)

function restoreScenarios() {
  const shared = readSharedPayload()
  const stored = shared ?? readStoredPayload()
  const restored = stored?.scenarios?.map((item) => hydrateScenario(item)) ?? []
  scenarios.value = restored.length ? restored : [createScenario()]

  if (!restored.length) syncBrandDefaults(scenarios.value[0])
  const requestedIndex = stored?.activeIndex ?? 0
  activeId.value = scenarios.value[Math.min(Math.max(requestedIndex, 0), scenarios.value.length - 1)].id
  nextId = Math.max(...scenarios.value.map((item) => item.id)) + 1
  if (shared) shareStatus.value = '已从分享链接恢复方案'
}

function hydrateScenario(raw: Partial<CalculationScenario>): CalculationScenario {
  const base = createScenario()
  const brand = brands.value.some((item) => item.brand === raw.brand) ? raw.brand! : base.brand
  const matchingRule = rules.value.find((item) => item.id === raw.ruleId && item.brand === brand)
  return {
    ...base,
    ...raw,
    id: base.id,
    brand,
    ruleId: matchingRule?.id ?? null,
    customRule: {
      ...base.customRule,
      ...(raw.customRule ?? {}),
      loss_type: 'percentage',
    },
    result: null,
    error: '',
    loading: false,
  }
}

function readStoredPayload(): SharedPayload | null {
  try {
    return parsePayload(localStorage.getItem(STORAGE_KEY))
  } catch {
    return null
  }
}

function readSharedPayload(): SharedPayload | null {
  try {
    const encoded = new URLSearchParams(window.location.search).get(SHARE_QUERY_KEY)
    if (!encoded) return null
    const normalized = encoded.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
    const bytes = Uint8Array.from(atob(padded), (char) => char.charCodeAt(0))
    return parsePayload(new TextDecoder().decode(bytes))
  } catch {
    return null
  }
}

interface SharedPayload {
  version: 1
  activeIndex: number
  scenarios: Partial<CalculationScenario>[]
}

function parsePayload(raw: string | null): SharedPayload | null {
  if (!raw) return null
  const payload = JSON.parse(raw) as SharedPayload
  if (payload.version !== 1 || !Array.isArray(payload.scenarios) || !payload.scenarios.length) return null
  return payload
}

function scenarioInput(scenario: CalculationScenario): Partial<CalculationScenario> {
  const { result: _result, error: _error, loading: _loading, ...input } = scenario
  return input
}

function sharePayload(): SharedPayload {
  return {
    version: 1,
    activeIndex: Math.max(0, scenarios.value.findIndex((item) => item.id === activeId.value)),
    scenarios: scenarios.value.map(scenarioInput),
  }
}

async function copyShareLink() {
  const bytes = new TextEncoder().encode(JSON.stringify(sharePayload()))
  const binary = Array.from(bytes, (byte) => String.fromCharCode(byte)).join('')
  const encoded = btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
  const url = new URL('/calculate', window.location.origin)
  url.searchParams.set(SHARE_QUERY_KEY, encoded)
  try {
    await navigator.clipboard.writeText(url.toString())
    shareStatus.value = '分享链接已复制，链接包含当前方案输入'
  } catch {
    shareStatus.value = '复制失败，请检查浏览器剪贴板权限'
  }
}

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
    loss_type: 'percentage',
    loss_value: rule.loss_value,
    // 工费由购买信息统一输入；临时规则不再承担工费和回收计价配置。
    labor_type: 'fixed',
    labor_value: 0,
    recycle_price_type: 'recycle',
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

function ruleLocation(rule: ExchangeRule) {
  return [rule.city, rule.store_name].filter(Boolean).join(' · ') || '未填写门店信息'
}

function laborRuleText(rule: ExchangeRule) {
  return rule.labor_type === 'perGram'
    ? `${rule.labor_value} 元/g`
    : `固定 ${rule.labor_value} 元`
}

function recycleRuleText(rule: ExchangeRule) {
  return rule.recycle_price_type === 'jewelry' ? '按饰品金价' : '按回收金价'
}

function extraGoldError(scenario: CalculationScenario) {
  if (!scenario.useOldGold) return ''
  const oldWeight = scenario.oldWeight ?? 0
  const newWeight = scenario.newWeight ?? 0
  const rule = scenario.customRule
  if (oldWeight <= 0 || !rule.need_extra_gold) return ''
  if (rule.extra_rate <= 0) return '该规则要求增金，请填写大于 0 的增金比例'

  const minNewWeight = oldWeight * (1 + rule.extra_rate / 100)
  if (newWeight + 1e-9 >= minNewWeight) return ''

  const actualRate = (newWeight - oldWeight) / oldWeight * 100
  return `增金比例不足：要求至少 ${rule.extra_rate.toFixed(2)}%（新金至少 ${minNewWeight.toFixed(2)}g），当前为 ${actualRate.toFixed(2)}%（${newWeight.toFixed(2)}g）`
}

function buildRequest(scenario: CalculationScenario): CostCalculationRequest | null {
  if (!scenario.brand || !scenario.newWeight || !scenario.newPrice) {
    scenario.error = '请填写品牌、重量和金价'
    return null
  }
  const laborFee = scenario.laborFee ?? 0
  if (laborFee < 0) {
    scenario.error = '工费不能小于 0'
    return null
  }
  if (scenario.useOldGold && (!scenario.oldWeight || scenario.oldWeight <= 0)) {
    scenario.error = '使用旧金置换时，请填写大于 0 的旧金重量'
    scenario.result = null
    return null
  }
  const extraError = extraGoldError(scenario)
  if (extraError) {
    scenario.error = extraError
    scenario.result = null
    return null
  }

  return {
    purchase: {
      brand: scenario.brand,
      new_weight: scenario.newWeight,
      new_price: scenario.newPrice,
      labor_fee: scenario.laborFeeType === 'perGram'
        ? Math.round(laborFee * scenario.newWeight * 100) / 100
        : laborFee,
      old_weight: scenario.useOldGold ? scenario.oldWeight ?? 0 : 0,
      old_purchase_cost: scenario.useOldGold ? scenario.oldPurchaseCost ?? 0 : 0,
      old_brand: scenario.useOldGold ? scenario.oldBrand || scenario.brand : null,
      old_is_bar: scenario.useOldGold && scenario.oldGoldType === 'bar',
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
  } catch (error) {
    scenario.result = null
    scenario.error = axios.isAxiosError(error) && typeof error.response?.data?.detail === 'string'
      ? error.response.data.detail
      : '计算失败，请检查输入或置换规则'
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
      <div class="page-actions">
        <button class="btn" :disabled="!scenarios.length" @click="copyShareLink">复制分享链接</button>
        <button class="btn" @click="addScenario()">+ 新增方案</button>
      </div>
    </div>
    <p v-if="shareStatus" class="share-status">{{ shareStatus }}</p>

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
        <h2 class="section-label">① 新金信息</h2>
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
        <div class="form-row field-space">
          <div class="form-group">
            <label>工费方式</label>
            <select v-model="activeScenario.laborFeeType">
              <option value="perGram">按克</option>
              <option value="perItem">按件</option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ activeScenario.laborFeeType === 'perGram' ? '工费 (元/g)' : '工费 (元/件)' }}</label>
            <input v-model.number="activeScenario.laborFee" type="number" step="0.01" min="0" />
          </div>
        </div>

        <h2 class="section-label old-gold-heading">② 旧金置换</h2>
        <label class="old-gold-toggle field-space">
          <input v-model="activeScenario.useOldGold" type="checkbox" />
          <span><strong>使用旧金置换</strong><small>开启后填写旧金信息；关闭则按直接购买计算</small></span>
        </label>
        <div v-if="activeScenario.useOldGold" class="old-gold-panel">
          <div class="form-row field-space">
            <div class="form-group">
              <label>旧金类型</label>
              <select v-model="activeScenario.oldGoldType">
                <option value="jewelry">饰品</option>
                <option value="bar">金条</option>
              </select>
            </div>
            <div class="form-group">
              <label>旧金品牌</label>
              <select v-model="activeScenario.oldBrand">
                <option value="">同新金品牌</option>
                <option v-for="b in brands" :key="b.brand" :value="b.brand">{{ b.brand_name }}</option>
              </select>
            </div>
          </div>
          <div class="form-row field-space">
            <div class="form-group"><label>旧金重量 (g)</label><input v-model.number="activeScenario.oldWeight" type="number" step="0.01" min="0.01" /></div>
            <div class="form-group"><label>旧金购买成本 (元)</label><input v-model.number="activeScenario.oldPurchaseCost" type="number" step="0.01" min="0" /></div>
          </div>
        </div>
        <h2 class="section-label">③ 门店规则与计算</h2>
        <div class="form-group rule-select">
          <label>规则模板</label>
          <select v-model="activeScenario.ruleId" :disabled="activeScenario.useCustomRule" @change="syncRule(activeScenario)">
            <option :value="null">默认规则</option>
            <option v-for="r in brandRules" :key="r.id" :value="r.id">{{ r.name }}</option>
          </select>
        </div>
        <label class="custom-toggle"><input v-model="activeScenario.useCustomRule" type="checkbox" /> 自定义规则</label>
        <section v-if="selectedTemplateRule" class="readonly-rule-panel" aria-label="已选规则详情">
          <div class="readonly-rule-head">
            <div>
              <strong>{{ selectedTemplateRule.name }}</strong>
              <small>{{ ruleLocation(selectedTemplateRule) }}</small>
            </div>
            <RouterLink class="btn compact" to="/rules">去规则管理修改</RouterLink>
          </div>
          <dl class="readonly-rule-grid">
            <div>
              <dt>金条置换</dt>
              <dd>{{ selectedTemplateRule.support_bar ? '支持' : '不支持' }}</dd>
            </div>
            <div>
              <dt>跨品牌置换</dt>
              <dd>{{ selectedTemplateRule.support_other_brand ? '支持' : '不支持' }}</dd>
            </div>
            <div>
              <dt>旧饰品置换</dt>
              <dd>{{ selectedTemplateRule.support_old_jewelry ? '支持' : '不支持' }}</dd>
            </div>
            <div>
              <dt>增金要求</dt>
              <dd>{{ selectedTemplateRule.need_extra_gold ? `至少 ${selectedTemplateRule.extra_rate}%` : '无' }}</dd>
            </div>
            <div>
              <dt>旧金损耗</dt>
              <dd>每克 {{ selectedTemplateRule.loss_value }}%</dd>
            </div>
            <div>
              <dt>工费规则</dt>
              <dd>{{ laborRuleText(selectedTemplateRule) }}</dd>
            </div>
            <div>
              <dt>旧金计价</dt>
              <dd>{{ recycleRuleText(selectedTemplateRule) }}</dd>
            </div>
          </dl>
          <p class="readonly-rule-hint">此处仅展示模板内容，具体规则只能在“规则”页面修改。</p>
        </section>
        <div v-if="activeScenario.useCustomRule" class="rule-panel">
          <div class="checkbox-row">
            <label><input v-model="activeScenario.customRule.support_bar" type="checkbox" /> 支持金条</label>
            <label><input v-model="activeScenario.customRule.support_other_brand" type="checkbox" /> 跨品牌</label>
            <label><input v-model="activeScenario.customRule.support_old_jewelry" type="checkbox" /> 旧饰品</label>
            <label><input v-model="activeScenario.customRule.need_extra_gold" type="checkbox" /> 要求增金</label>
          </div>
          <div v-if="activeScenario.customRule.need_extra_gold" class="form-group rule-row">
            <label>增金比例 (%)</label><input v-model.number="activeScenario.customRule.extra_rate" type="number" min="0" />
          </div>
          <div class="form-group rule-row">
            <label>旧金损耗（每克 %）</label>
            <input v-model.number="activeScenario.customRule.loss_value" type="number" min="0" max="100" step="0.01" />
          </div>
        </div>
        <p v-if="extraGoldError(activeScenario)" class="error rule-error">{{ extraGoldError(activeScenario) }}</p>
        <button class="btn btn-primary calc-btn" :disabled="activeScenario.loading || !!extraGoldError(activeScenario)" @click="calculateScenario(activeScenario)">
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
.page-heading,.page-actions,.comparison-heading,.scenario-actions,.comparison-name{display:flex;align-items:center;justify-content:space-between;gap:1rem}.page-heading{margin-bottom:1rem}.page-actions{gap:.5rem}.page-heading .page-title{margin-bottom:.15rem}.share-status{padding:.55rem .75rem;margin:-.25rem 0 .75rem;border-radius:6px;background:var(--warn-bg);color:#76520a;font-size:.8rem}.scenario-bar{display:flex;gap:.5rem;overflow-x:auto;margin-bottom:.75rem;padding-bottom:.15rem}.scenario-tab{min-width:120px;padding:.65rem .9rem;border:1px solid var(--border);border-radius:7px;background:var(--surface);text-align:left}.scenario-tab span,.scenario-tab small{display:block}.scenario-tab small{color:var(--text-muted);font-size:.72rem}.scenario-tab.active{border-color:var(--gold);box-shadow:inset 0 -2px var(--gold)}.scenario-actions{justify-content:flex-start;padding:.75rem;margin-bottom:1rem}.scenario-actions input{min-width:0;width:220px;padding:.5rem .65rem;border:1px solid var(--border);border-radius:6px;font-weight:600}.compact{padding:.45rem .75rem;font-size:.82rem}.calc-layout{display:grid;grid-template-columns:1fr 1fr;gap:1rem;align-items:start}.section-label{font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--text-muted);margin-bottom:1rem}.old-gold-heading{margin-top:.25rem}.old-gold-toggle{display:flex;align-items:flex-start;gap:.55rem;padding:.75rem;border:1px solid var(--border);border-radius:6px;cursor:pointer}.old-gold-toggle input{margin-top:.25rem}.old-gold-toggle span,.old-gold-toggle small{display:block}.old-gold-toggle strong{font-size:.88rem}.old-gold-toggle small{color:var(--text-muted);font-size:.76rem}.old-gold-panel{padding:.85rem;margin-bottom:1rem;border-radius:6px;background:var(--bg)}.old-gold-panel .field-space:last-child{margin-bottom:0}.field-space{margin-bottom:1rem}.rule-select{margin-bottom:.75rem}.custom-toggle{display:flex;align-items:center;gap:.4rem;font-size:.875rem;margin-bottom:.75rem;cursor:pointer}.rule-panel{padding:.75rem;background:var(--bg);border-radius:6px;margin-bottom:1rem}.rule-row{margin-top:.75rem}.calc-btn{width:100%;margin-top:.5rem}.error{color:var(--danger);font-size:.85rem;margin-top:.75rem;text-align:center}.highlight{text-align:center;padding:1rem 0 1.25rem;border-bottom:1px solid var(--border);margin-bottom:1rem}.best-badge{display:inline-block;padding:.15rem .45rem;border-radius:999px;background:#fff4cc;color:#8a6500;font-size:.7rem;font-weight:700}.final-cost{font-size:2rem;font-weight:600}.per-gram{font-size:.9rem;margin-top:.25rem}.per-gram strong{color:var(--gold)}.per-gram small{color:var(--text-muted);margin-left:.35rem}.result-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-bottom:1rem}.result-summary>div{padding:.75rem;border:1px solid var(--border);border-radius:6px;background:var(--bg)}.result-summary span{display:block;color:var(--text-muted);font-size:.75rem;margin-bottom:.35rem}.result-summary strong{display:block;font-size:1rem}.result-summary .saved strong{color:#1f8f4d}.result-summary .extra strong{color:var(--danger)}.breakdown{list-style:none}.breakdown li{display:flex;justify-content:space-between;padding:.45rem 0;font-size:.875rem;border-bottom:1px solid var(--border)}.breakdown small{color:var(--text-muted)}.warnings{list-style:none;margin-top:1rem}.warnings li{font-size:.8rem;color:#856404;background:var(--warn-bg);padding:.5rem .75rem;border-radius:4px;margin-bottom:.35rem}.empty{text-align:center;padding:3rem 0}.comparison{margin-top:1rem}.comparison-heading{margin-bottom:1rem}.comparison-heading h2{font-size:1rem}.comparison-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.75rem}.comparison-item{padding:1rem;border:1px solid var(--border);border-radius:7px;cursor:pointer}.comparison-item:hover{border-color:#ccc}.comparison-item.best{border-color:var(--gold);background:#fffdf5}.comparison-price{font-size:1.35rem;font-weight:700;color:var(--gold);margin:.75rem 0}.comparison-price small{font-size:.75rem}.comparison-item dl>div{display:flex;justify-content:space-between;font-size:.78rem;margin-top:.35rem}.comparison-item dt{color:var(--text-muted)}.comparison-item dd{font-weight:600}.uncalculated{padding:1.5rem 0;text-align:center}
.readonly-rule-panel{padding:.85rem;margin-bottom:1rem;border:1px solid #eadca9;border-radius:7px;background:#fffdf5}.readonly-rule-head{display:flex;align-items:flex-start;justify-content:space-between;gap:.75rem}.readonly-rule-head strong,.readonly-rule-head small{display:block}.readonly-rule-head strong{font-size:.92rem}.readonly-rule-head small{margin-top:.2rem;color:var(--text-muted);font-size:.75rem}.readonly-rule-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.5rem;margin:.8rem 0}.readonly-rule-grid>div{padding:.55rem .65rem;border:1px solid var(--border);border-radius:5px;background:var(--surface)}.readonly-rule-grid dt{margin-bottom:.18rem;color:var(--text-muted);font-size:.72rem}.readonly-rule-grid dd{font-size:.82rem;font-weight:600}.readonly-rule-hint{color:var(--text-muted);font-size:.75rem}
@media(max-width:768px){.calc-layout{grid-template-columns:1fr}.result-summary{grid-template-columns:1fr}.comparison-heading{align-items:flex-start;flex-direction:column}.comparison-heading .btn{width:100%}}
@media(max-width:520px){.page-heading{align-items:flex-start}.page-actions{align-items:stretch;flex-direction:column}.page-actions .btn{width:100%}.scenario-actions{flex-wrap:wrap}.scenario-actions input{width:100%}.readonly-rule-head{flex-direction:column}.readonly-rule-head .btn{width:100%}.readonly-rule-grid{grid-template-columns:1fr}}
</style>
