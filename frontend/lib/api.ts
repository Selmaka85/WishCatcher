import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface WishData {
  id: string
  intent: string
  domain: string
  source: string
  score: number
  business_score: number
  feasibility: string
  technologies: string[]
  timestamp: string
  trigger_analysis?: {
    trigger?: { text?: string }
    pain_points?: { text: string; severity?: string }[]
    emotional_intensity?: number
  } | null
  market_analysis?: {
    market_size?: string
    target_demographic?: string
    [key: string]: unknown
  } | null
  monetization?: {
    model?: string
    estimated_price?: string
    potential_revenue?: string
    [key: string]: unknown
  } | null
}
export interface ProductGap {
  product_name: string
  emag_status: string
  amazon_uk_price?: number | null
  emag_price?: number | null
  image_url?: string | null
  profit_margin?: number | null
  risk_level: string
}
export interface FBAAnalysis {
  profit_brut: number
  profit_net: number
  roi: number
  break_even_units: number
  risk_level: string
  recommendation: string
}
export const wishesApi = {
  async collect(sources: string[], filters: object, limit: number) {
    const { data } = await axios.post<{wishes: WishData[]; total: number; filters_applied: unknown}>(
      API_URL + '/api/wishes/collect', { sources, filters, limit }
    )
    return data
  },
}
export const businessPlansApi = {
  async generate(wish_id: string, include_financials: boolean) {
    const { data } = await axios.post(API_URL + '/api/business-plans/generate', {
      wish_id, include_financials, include_market_analysis: true,
    })
    return data
  },
}
export const mvpApi = {
  async generate(wish_id: string, business_plan_id?: string) {
    const { data } = await axios.post(API_URL + '/api/mvp/generate', {
      wish_id, business_plan_id,
    })
    return data
  },
}
export const productGapsApi = {
  async search(category: string, max_price?: number, search_volume = false) {
    const { data } = await axios.post<{gaps: ProductGap[]; total_found: number}>(
      API_URL + '/api/product-gaps/search', {
        category, max_price, search_volume,
      }
    )
    return data
  },
  async calculateFBA(amazon_price: number, import_costs: number,
                     fba_costs: number, selling_price: number, quantity: number) {
    const { data } = await axios.post<FBAAnalysis>(
      API_URL + '/api/product-gaps/fba', {
        amazon_price, import_costs, fba_costs, selling_price, quantity,
      }
    )
    return data
  },
}
