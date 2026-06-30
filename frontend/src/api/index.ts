import axios from 'axios'
import type {
  CostCalculationRequest,
  CostCalculationResult,
  ExchangeRule,
  ExchangeRuleInput,
  GoldPriceOverview,
} from '@/types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
})

export async function fetchPrices(): Promise<GoldPriceOverview> {
  const { data } = await api.get<GoldPriceOverview>('/api/prices')
  return data
}

export async function updatePrices(payload: {
  domestic_price?: number
  brands?: GoldPriceOverview['brands']
}): Promise<GoldPriceOverview> {
  const { data } = await api.put<GoldPriceOverview>('/api/prices', payload)
  return data
}

export async function fetchRules(brand?: string): Promise<ExchangeRule[]> {
  const { data } = await api.get<ExchangeRule[]>('/api/rules', { params: { brand } })
  return data
}

export async function createRule(rule: ExchangeRuleInput): Promise<ExchangeRule> {
  const { data } = await api.post<ExchangeRule>('/api/rules', rule)
  return data
}

export async function updateRule(id: number, rule: ExchangeRuleInput): Promise<ExchangeRule> {
  const { data } = await api.put<ExchangeRule>(`/api/rules/${id}`, rule)
  return data
}

export async function deleteRule(id: number): Promise<void> {
  await api.delete(`/api/rules/${id}`)
}

export async function calculateCost(request: CostCalculationRequest): Promise<CostCalculationResult> {
  const { data } = await api.post<CostCalculationResult>('/api/calculate', request)
  return data
}

export async function healthCheck(): Promise<{ status: string }> {
  const { data } = await api.get('/health')
  return data
}
