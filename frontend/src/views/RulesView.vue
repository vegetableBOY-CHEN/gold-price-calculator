<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchRules, fetchPrices, createRule, updateRule, deleteRule } from '@/api'
import type { ExchangeRule, ExchangeRuleInput } from '@/types'

const rules = ref<ExchangeRule[]>([])
const brands = ref<{ brand: string; brand_name: string }[]>([])
const showForm = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)

const emptyForm = (): ExchangeRuleInput => ({
  name: '',
  brand: 'chow_tai_fook',
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
})

const form = ref<ExchangeRuleInput>(emptyForm())

onMounted(load)

async function load() {
  const [ruleData, priceData] = await Promise.all([fetchRules(), fetchPrices()])
  rules.value = ruleData
  brands.value = priceData.brands.map((b) => ({ brand: b.brand, brand_name: b.brand_name }))
}

function brandName(id: string) {
  return brands.value.find((b) => b.brand === id)?.brand_name ?? id
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  showForm.value = true
}

function openEdit(rule: ExchangeRule) {
  editingId.value = rule.id ?? null
  form.value = {
    name: rule.name,
    brand: rule.brand,
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
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  editingId.value = null
}

async function saveForm() {
  if (!form.value.name.trim()) return
  saving.value = true
  try {
    if (editingId.value) {
      await updateRule(editingId.value, form.value)
    } else {
      await createRule(form.value)
    }
    await load()
    cancelForm()
  } finally {
    saving.value = false
  }
}

async function remove(id: number) {
  if (!confirm('确定删除此规则？')) return
  await deleteRule(id)
  await load()
}

function ruleSummary(r: ExchangeRule) {
  const parts: string[] = []
  if (r.need_extra_gold) parts.push(`增金${r.extra_rate}%`)
  if (r.loss_type === 'fixed' && r.loss_value) parts.push(`损耗${r.loss_value}g`)
  if (r.loss_type === 'percentage' && r.loss_value) parts.push(`损耗${r.loss_value}%`)
  parts.push(r.labor_type === 'perGram' ? `工费${r.labor_value}元/g` : `工费${r.labor_value}元`)
  return parts.join(' · ') || '无特殊规则'
}
</script>

<template>
  <div>
    <div class="page-head">
      <h1 class="page-title">门店规则</h1>
      <button class="btn btn-primary" @click="openCreate">新增规则</button>
    </div>

    <div v-if="showForm" class="card form-card">
      <h2 class="form-title">{{ editingId ? '编辑规则' : '新增规则' }}</h2>

      <div class="form-row" style="margin-bottom: 1rem">
        <div class="form-group">
          <label>模板名称</label>
          <input v-model="form.name" type="text" placeholder="如：周大福XX店" />
        </div>
        <div class="form-group">
          <label>品牌</label>
          <select v-model="form.brand">
            <option v-for="b in brands" :key="b.brand" :value="b.brand">{{ b.brand_name }}</option>
          </select>
        </div>
      </div>

      <div class="checkbox-row" style="margin-bottom: 1rem">
        <label><input v-model="form.support_bar" type="checkbox" /> 支持金条置换</label>
        <label><input v-model="form.support_other_brand" type="checkbox" /> 支持跨品牌</label>
        <label><input v-model="form.support_old_jewelry" type="checkbox" /> 支持旧饰品</label>
        <label><input v-model="form.need_extra_gold" type="checkbox" /> 要求增金</label>
      </div>

      <div class="form-row form-row-3" style="margin-bottom: 1rem">
        <div class="form-group">
          <label>增金比例 (%)</label>
          <input v-model.number="form.extra_rate" type="number" min="0" />
        </div>
        <div class="form-group">
          <label>损耗类型</label>
          <select v-model="form.loss_type">
            <option value="fixed">固定克数</option>
            <option value="percentage">百分比</option>
          </select>
        </div>
        <div class="form-group">
          <label>损耗值</label>
          <input v-model.number="form.loss_value" type="number" min="0" step="0.01" />
        </div>
      </div>

      <div class="form-row form-row-3" style="margin-bottom: 1rem">
        <div class="form-group">
          <label>工费类型</label>
          <select v-model="form.labor_type">
            <option value="fixed">固定工费</option>
            <option value="perGram">按克收费</option>
          </select>
        </div>
        <div class="form-group">
          <label>工费值</label>
          <input v-model.number="form.labor_value" type="number" min="0" />
        </div>
        <div class="form-group">
          <label>回收计价</label>
          <select v-model="form.recycle_price_type">
            <option value="recycle">按回收价</option>
            <option value="jewelry">按饰品价</option>
          </select>
        </div>
      </div>

      <div class="form-actions">
        <button class="btn" @click="cancelForm">取消</button>
        <button class="btn btn-primary" :disabled="saving" @click="saveForm">保存</button>
      </div>
    </div>

    <div class="rule-list">
      <div v-for="rule in rules" :key="rule.id" class="card rule-item">
        <div class="rule-head">
          <div>
            <p class="rule-name">{{ rule.name }}</p>
            <p class="text-muted">{{ brandName(rule.brand) }}</p>
          </div>
          <div class="rule-actions">
            <button class="btn btn-sm" @click="openEdit(rule)">编辑</button>
            <button class="btn btn-sm btn-danger" @click="remove(rule.id!)">删除</button>
          </div>
        </div>
        <p class="rule-summary">{{ ruleSummary(rule) }}</p>
        <div class="rule-tags">
          <span v-if="rule.support_bar" class="tag">金条</span>
          <span v-if="rule.support_other_brand" class="tag">跨品牌</span>
          <span v-if="rule.support_old_jewelry" class="tag">旧饰品</span>
        </div>
      </div>
      <p v-if="!rules.length" class="text-muted empty">暂无规则，点击上方新增</p>
    </div>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-head .page-title {
  margin-bottom: 0;
}

.form-card {
  margin-bottom: 1.5rem;
}

.form-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.rule-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.rule-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.rule-name {
  font-weight: 600;
  font-size: 0.95rem;
}

.rule-actions {
  display: flex;
  gap: 0.35rem;
}

.btn-sm {
  padding: 0.3rem 0.65rem;
  font-size: 0.8rem;
}

.rule-summary {
  font-size: 0.85rem;
  margin: 0.5rem 0;
  color: var(--text-muted);
}

.rule-tags {
  display: flex;
  gap: 0.35rem;
}

.tag {
  font-size: 0.7rem;
  padding: 0.15rem 0.5rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-muted);
}

.empty {
  text-align: center;
  padding: 2rem;
}
</style>
