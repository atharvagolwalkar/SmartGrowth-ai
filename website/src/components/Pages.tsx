'use client'
import { useState } from 'react'
import { api, HighRiskCustomer, ChurnPrediction } from '../lib/api'
import { SectionHeader, Spinner, ErrorState, RiskBadge, RiskBar, DataRow, StatCard } from '../components/UI'
import { Search, AlertTriangle, Download, DollarSign, Users } from 'lucide-react'

// ── Customer Analysis ─────────────────────────────────────────────────────────
export function CustomerAnalysis() {
  const [id,      setId]      = useState('')
  const [cust,    setCust]    = useState<any>(null)
  const [pred,    setPred]    = useState<ChurnPrediction | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const lookup = async (customerId: string) => {
    if (!customerId.trim()) return
    setLoading(true); setError(''); setCust(null); setPred(null)
    try {
      const [c, p] = await Promise.all([api.customer(customerId), api.predictChurn(customerId)])
      setCust(c); setPred(p)
    } catch (e: any) { setError(`Customer not found: ${customerId}`) }
    finally { setLoading(false) }
  }

  const prob = pred?.churn_probability || 0
  const riskColor = pred?.risk_level === 'High' ? '#EF4444' : pred?.risk_level === 'Medium' ? '#F59E0B' : '#10B981'

  return (
    <div>
      <SectionHeader title="Customer Analysis" subtitle="Individual churn risk and profile lookup" />

      <div className="card p-4 mb-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              value={id}
              onChange={e => setId(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && lookup(id)}
              placeholder="Enter customer ID — e.g. 7590-VHVEG"
              className="w-full bg-surface2 border border-border rounded-lg pl-9 pr-4 py-2.5 text-sm text-text placeholder:text-muted outline-none focus:border-accent transition-colors"
            />
          </div>
          <button onClick={() => lookup(id)}
            className="px-5 py-2.5 bg-accent hover:bg-accent/80 text-white rounded-lg text-sm font-medium transition-colors">
            Analyse
          </button>
        </div>
        <p className="text-xs text-muted mt-2">Try: 7590-VHVEG · 5575-GNVDE · 3668-QPYBK</p>
      </div>

      {loading ? <Spinner /> : error ? <ErrorState message={error} /> : cust && pred ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

          {/* Profile */}
          <div className="lg:col-span-3 card p-5">
            <div className="text-xs text-muted uppercase tracking-wider mb-4">Customer Profile</div>
            <DataRow label="Customer ID"      value={cust.customer_id} />
            <DataRow label="Gender"           value={cust.gender} />
            <DataRow label="Senior Citizen"   value={cust.senior_citizen ? 'Yes' : 'No'} />
            <DataRow label="Partner"          value={cust.partner ? 'Yes' : 'No'} />
            <DataRow label="Dependents"       value={cust.dependents ? 'Yes' : 'No'} />
            <DataRow label="Tenure"           value={`${cust.tenure} months`} />
            <DataRow label="Contract"         value={cust.contract} />
            <DataRow label="Internet Service" value={cust.internet_service} />
            <DataRow label="Monthly Charges"  value={`$${(cust.monthly_charges||0).toFixed(2)}`} />
            <DataRow label="Total Charges"    value={`$${parseFloat(cust.total_charges||0).toFixed(2)}`} />
            <DataRow label="Payment Method"   value={cust.payment_method} />
          </div>

          {/* Risk panel */}
          <div className="lg:col-span-2 space-y-4">
            <div className="card p-5">
              <div className="text-xs text-muted uppercase tracking-wider mb-4">Churn Risk</div>
              <div className="text-center mb-4">
                <div className="text-5xl font-bold font-mono mb-1" style={{ color: riskColor }}>
                  {(prob * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-muted mb-3">churn probability</div>
                <RiskBadge level={pred.risk_level} />
              </div>
              <div className="mb-2">
                <div className="flex justify-between text-xs text-muted mb-1.5">
                  <span>Risk level</span><span style={{ color: riskColor }}>{pred.risk_level}</span>
                </div>
                <RiskBar value={prob} />
              </div>
            </div>

            {pred.recommendations && pred.recommendations.length > 0 && (
              <div className="card p-5">
                <div className="text-xs text-muted uppercase tracking-wider mb-3">Recommendations</div>
                <div className="space-y-2">
                  {pred.recommendations.slice(0,4).map((r, i) => (
                    <div key={i} className="flex gap-2 text-sm text-muted leading-relaxed">
                      <span className="text-accent mt-0.5 shrink-0">→</span>
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="card p-16 text-center">
          <div className="text-4xl mb-3">🔍</div>
          <div className="text-muted text-sm">Enter a customer ID above to see their full profile and churn risk score.</div>
        </div>
      )}
    </div>
  )
}

// ── High Risk ─────────────────────────────────────────────────────────────────
export function HighRisk() {
  const [customers, setCustomers] = useState<HighRiskCustomer[]>([])
  const [loading, setLoading] = useState(false)
  const [loaded,  setLoaded]  = useState(false)
  const [error,   setError]   = useState('')

  const load = async () => {
    setLoading(true); setError('')
    try {
      const d = await api.highRisk(100)
      setCustomers(d.high_risk_customers || [])
      setLoaded(true)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  const totalRevRisk = customers.reduce((s, c) => s + (c.monthly_charges || 0), 0)
  const avgProb = customers.length ? customers.reduce((s, c) => s + c.churn_probability, 0) / customers.length : 0

  return (
    <div>
      <SectionHeader title="High Risk Customers" subtitle="Customers with churn probability ≥ 60%" />

      {!loaded ? (
        <div className="card p-12 text-center">
          <AlertTriangle size={32} className="text-danger mx-auto mb-4 opacity-60" />
          <p className="text-muted text-sm mb-4">Scan your customer base for high churn risk.</p>
          <button onClick={load} disabled={loading}
            className="px-6 py-2.5 bg-danger hover:bg-danger/80 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
            {loading ? 'Scanning...' : 'Run Risk Scan'}
          </button>
        </div>
      ) : loading ? <Spinner /> : error ? <ErrorState message={error} /> : (
        <>
          <div className="grid grid-cols-3 gap-3 mb-6 stagger">
            <StatCard label="High Risk Count"     value={customers.length.toLocaleString()}        icon={<Users size={14}/>}       accent="#EF4444" />
            <StatCard label="Avg Churn Prob"      value={`${(avgProb*100).toFixed(1)}%`}           icon={<AlertTriangle size={14}/>} accent="#F59E0B" />
            <StatCard label="Monthly Rev at Risk" value={`$${totalRevRisk.toLocaleString(undefined,{maximumFractionDigits:0})}`} icon={<DollarSign size={14}/>} accent="#EF4444" />
          </div>

          <div className="space-y-2">
            {customers
              .sort((a, b) => b.churn_probability - a.churn_probability)
              .slice(0, 30)
              .map((c, i) => (
                <div key={c.customer_id} className="card p-4 hover:border-red-900/40 transition-all animate-fade-up"
                     style={{ animationDelay:`${i*20}ms`, animationFillMode:'forwards', opacity:0 }}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm font-medium">{c.customer_id}</span>
                      <RiskBadge level={c.risk_level} />
                    </div>
                    <span className="text-lg font-bold font-mono" style={{
                      color: c.churn_probability > 0.7 ? '#EF4444' : c.churn_probability > 0.4 ? '#F59E0B' : '#10B981'
                    }}>
                      {(c.churn_probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <RiskBar value={c.churn_probability} />
                  <div className="flex gap-4 mt-2 text-xs text-muted">
                    <span>Tenure: {c.tenure_months} mo</span>
                    <span>Monthly: ${(c.monthly_charges||0).toFixed(0)}</span>
                  </div>
                </div>
              ))}
          </div>
        </>
      )}
    </div>
  )
}

// ── Batch Predict ─────────────────────────────────────────────────────────────
export function BatchPredict() {
  const [ids,     setIds]     = useState('')
  const [results, setResults] = useState<ChurnPrediction[]>([])
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const run = async () => {
    const parsed = ids.split(/[\n,]/).map(s => s.trim()).filter(Boolean)
    if (!parsed.length) return
    setLoading(true); setError(''); setResults([])
    try {
      const d = await api.batchPredict(parsed)
      setResults(d.batch_results || [])
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  const download = () => {
    const csv = [
      'customer_id,churn_probability,risk_level,churn_prediction',
      ...results.map(r => `${r.customer_id},${r.churn_probability},${r.risk_level},${r.churn_prediction}`)
    ].join('\n')
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
    a.download = `churn_batch_${Date.now()}.csv`
    a.click()
  }

  const high   = results.filter(r => r.risk_level === 'High').length
  const medium = results.filter(r => r.risk_level === 'Medium').length
  const low    = results.filter(r => r.risk_level === 'Low').length

  return (
    <div>
      <SectionHeader title="Batch Prediction" subtitle="Run churn predictions for multiple customers at once" />

      <div className="card p-5 mb-6">
        <div className="text-xs text-muted uppercase tracking-wider mb-3">Customer IDs</div>
        <textarea
          value={ids} onChange={e => setIds(e.target.value)}
          placeholder={'7590-VHVEG\n5575-GNVDE\n3668-QPYBK'}
          rows={5}
          className="w-full bg-surface2 border border-border rounded-lg px-4 py-3 text-sm text-text placeholder:text-muted outline-none focus:border-accent transition-colors font-mono resize-none"
        />
        <div className="flex items-center justify-between mt-3">
          <span className="text-xs text-muted">{ids.split(/[\n,]/).filter(s=>s.trim()).length} IDs entered</span>
          <button onClick={run} disabled={loading}
            className="px-5 py-2 bg-accent hover:bg-accent/80 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
            {loading ? 'Running...' : 'Run Predictions →'}
          </button>
        </div>
      </div>

      {loading ? <Spinner /> : error ? <ErrorState message={error} /> : results.length > 0 && (
        <>
          <div className="grid grid-cols-4 gap-3 mb-4 stagger">
            <StatCard label="Processed" value={results.length} />
            <StatCard label="High Risk"   value={high}   accent="#EF4444" />
            <StatCard label="Medium Risk" value={medium} accent="#F59E0B" />
            <StatCard label="Low Risk"    value={low}    accent="#10B981" />
          </div>

          <div className="card overflow-hidden mb-4">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border">
              <span className="text-xs text-muted uppercase tracking-wider">Results</span>
              <button onClick={download}
                className="flex items-center gap-1.5 text-xs text-accent hover:text-accent/70 transition-colors">
                <Download size={12} /> Download CSV
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-muted text-xs uppercase tracking-wider border-b border-border">
                    <th className="text-left px-5 py-3">Customer ID</th>
                    <th className="text-right px-5 py-3">Probability</th>
                    <th className="text-right px-5 py-3">Risk</th>
                    <th className="text-right px-5 py-3">Prediction</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {results.map(r => (
                    <tr key={r.customer_id} className="hover:bg-surface2/50 transition-colors">
                      <td className="px-5 py-3 font-mono text-xs">{r.customer_id}</td>
                      <td className="px-5 py-3 text-right font-mono">{(r.churn_probability*100).toFixed(1)}%</td>
                      <td className="px-5 py-3 text-right"><RiskBadge level={r.risk_level} /></td>
                      <td className="px-5 py-3 text-right">
                        <span className={r.churn_prediction ? 'text-red-400' : 'text-emerald-400'}>
                          {r.churn_prediction ? 'Will Churn' : 'Retained'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
