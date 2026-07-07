export interface GoldPriceItem {
  brand: string
  brand_name: string
  gold_price: number
  bar_price?: number | null
  update_time?: string | null
}

export interface DomesticGoldPrice {
  price: number
  update_time?: string | null
}

export interface MarketGoldPrice {
  market: 'international' | 'domestic' | string
  name: string
  symbol: string
  exchange?: string | null
  price: number
  currency: string
  unit: string
  change?: number | null
  change_percent?: number | null
  source: string
  status: 'live' | 'fallback' | string
  update_time?: string | null
}

export interface GoldPriceOverview {
  domestic: DomesticGoldPrice
  international: MarketGoldPrice[]
  domestic_markets: MarketGoldPrice[]
  brands: GoldPriceItem[]
  brand_refresh_interval_seconds: number
  market_refresh_interval_seconds: number
  server_time?: string | null
}

export interface ExchangeRule {
  id?: number
  name: string
  brand: string
  support_bar: boolean
  support_other_brand: boolean
  support_old_jewelry: boolean
  need_extra_gold: boolean
  extra_rate: number
  loss_type: 'fixed' | 'percentage'
  loss_value: number
  labor_type: 'fixed' | 'perGram'
  labor_value: number
  recycle_price_type: 'recycle' | 'jewelry'
  created_at?: string
  updated_at?: string
}

export type ExchangeRuleInput = Omit<ExchangeRule, 'id' | 'created_at' | 'updated_at'>

export interface PurchaseInfo {
  brand: string
  new_weight: number
  new_price: number
  labor_fee?: number | null
  old_weight: number
  old_purchase_cost?: number | null
  old_brand?: string | null
  old_is_bar: boolean
  recycle_price?: number | null
}

export interface ExchangeRuleInline {
  support_bar: boolean
  support_other_brand: boolean
  support_old_jewelry: boolean
  need_extra_gold: boolean
  extra_rate: number
  loss_type: 'fixed' | 'percentage'
  loss_value: number
  labor_type: 'fixed' | 'perGram'
  labor_value: number
  recycle_price_type: 'recycle' | 'jewelry'
}

export interface CostBreakdownItem {
  label: string
  value: number
  detail?: string | null
}

export interface CostCalculationResult {
  brand: string
  new_gold_total: number
  labor_fee: number
  old_weight: number
  loss_amount: number
  exchangeable_weight: number
  recycle_price: number
  old_gold_deduction: number
  direct_purchase_cost: number
  actual_cost: number
  savings_amount: number
  final_cost: number
  price_per_gram: number
  min_new_weight?: number | null
  breakdown: CostBreakdownItem[]
  warnings: string[]
}

export interface CostCalculationRequest {
  purchase: PurchaseInfo
  rule_id?: number | null
  exchange_rule?: ExchangeRuleInline | null
}

export const BRAND_LABELS: Record<string, string> = {
  chow_tai_fook: '周大福',
  chow_sang_sang: '周生生',
  lao_feng_xiang: '老凤祥',
  china_gold: '中国黄金',
  lao_miao: '老庙黄金',
  lukfook: '六福珠宝',
}
