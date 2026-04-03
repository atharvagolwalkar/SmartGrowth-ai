const BASE = process.env.NEXT_PUBLIC_API_URL || 'https://handhelds-cooling-gale-consistently.trycloudflare.com'
console.log("API Base URL:", BASE);   // Helpful for debugging on Vercel
async function req<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(BASE + path)
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)))
  const res = await fetch(url.toString())
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json()
}

export const api = {
  health:       () => req<{ status: string }>('/health'),
  customers:    (limit = 200) => req<{ customers: Customer[]; total_count: number }>('/customers/all', { limit }),
  customer:     (id: string) => req<Customer>(`/customer/${id}`),
  highRisk:     (limit = 50) => req<{ high_risk_customers: HighRiskCustomer[] }>('/customers/high-risk', { limit }),
  predictChurn: (id: string) => req<ChurnPrediction>(`/predict/churn/${id}`),
  batchPredict: (ids: string[]) => post<{ batch_results: ChurnPrediction[] }>('/predict/churn/batch', { customer_ids: ids }),

  forecast:     (horizon = 30, model = 'best') =>
    req<ForecastResponse>('/forecast/predict', { horizon, model }),
  forecastAll:  (horizon = 30) =>
    req<ForecastAllResponse>('/forecast/predict/all', { horizon }),
  forecastMetrics: () => req<ForecastMetrics>('/forecast/metrics'),

  nlpSearch:    (q: string, top_k = 8) =>
    req<NLPSearchResponse>('/nlp/search', { q, top_k }),
  nlpTimeline:  (freq = 'W') =>
    req<NLPTimelineResponse>('/nlp/sentiment/timeline', { freq }),
  nlpSummary:   () => req<NLPSummary>('/nlp/sentiment/summary'),
  nlpStats:     () => req<NLPStats>('/nlp/stats'),
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Customer {
  customer_id: string
  gender: string
  senior_citizen: boolean | number
  partner: boolean | number
  dependents: boolean | number
  tenure_months: number
  subscription_type: string
  monthly_charges: number
  total_charges: number | string
  churn_status: number | boolean
  payment_method?: string
  phone_service?: string
  multiple_lines?: string
  online_security?: string
  tech_support?: string
}

// Legacy interface for backwards compatibility
export interface CustomerLegacy extends Customer {
  tenure?: number
  contract?: string
  internet_service?: string
  churn?: boolean
}

export interface HighRiskCustomer {
  customer_id: string
  churn_probability: number
  risk_level: string
  monthly_charges: number
  tenure_months: number
  contract?: string
}

export interface ChurnPrediction {
  customer_id: string
  churn_probability: number
  churn_prediction: boolean
  risk_level: string
  recommendations?: string[]
}

export interface ForecastPoint {
  date: string
  forecast: number
  lower_bound: number
  upper_bound: number
  model: string
}

export interface ForecastResponse {
  model_used: string
  horizon_days: number
  forecast: ForecastPoint[]
  business_summary: {
    total_forecast_units: number
    avg_daily_demand: number
    peak_day: string
    peak_demand: number
    trough_day: string
    trough_demand: number
    demand_volatility: number
  }
}

export interface ForecastAllResponse {
  horizon_days: number
  best_model: string
  forecasts: Record<string, Array<{ date: string; forecast: number; lower_bound: number; upper_bound: number }>>
}

export interface ForecastMetrics {
  best_model: string
  holdout_days: number
  models: Record<string, { MAE: number; RMSE: number; MAPE: number; fit_time_s: number }>
}

export interface NLPSearchResult {
  feedback_id: string
  feedback_text: string
  similarity_score: number
  sentiment_label?: string
  category?: string
  channel?: string
  customer_id?: string
}

export interface NLPSearchResponse {
  query: string
  backend: string
  results: NLPSearchResult[]
  result_count: number
}

export interface NLPTimelinePoint {
  period: string
  positive_pct: number
  negative_pct: number
  neutral_pct: number
  net_sentiment: number
  total_count: number
}

export interface NLPTimelineResponse {
  timeline: NLPTimelinePoint[]
  trend: { direction: string; magnitude: number; summary: string }
}

export interface NLPSummary {
  total_feedback: number
  overall: Record<string, number>
  by_category: Record<string, Record<string, number>>
  by_channel: Record<string, Record<string, number>>
}

export interface NLPStats {
  total_feedback: number
  sentiment_distribution: Record<string, number>
  index_stats: { backend: string; document_count: number }
  trend?: { direction: string; summary: string }
}