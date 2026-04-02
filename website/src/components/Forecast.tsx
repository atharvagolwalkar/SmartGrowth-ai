'use client'
import { useEffect, useState } from 'react'
import { AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { api, ForecastResponse, ForecastAllResponse, ForecastMetrics } from '@/lib/api'
import { StatCard, SectionHeader, Spinner, ErrorState, TabBar } from '@/components/UI'
import { TrendingUp, Target, Zap, Clock } from 'lucide-react'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface2 border border-border rounded-lg px-3 py-2 text-xs space-y-1">
      <div className="text-muted font-medium">{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} style={{ color: p.color }}>{p.name}: {Number(p.value).toLocaleString(undefined,{maximumFractionDigits:1})}</div>
      ))}
    </div>
  )
}

const MODEL_COLORS: Record<string, string> = {
  'ARIMA': '#F59E0B', 'Prophet': '#10B981', 'N-BEATS': '#3B82F6',
}

export default function Forecast() {
  const [tab,      setTab]      = useState('Single Model')
  const [model,    setModel]    = useState('best')
  const [horizon,  setHorizon]  = useState(30)
  const [single,   setSingle]   = useState<ForecastResponse | null>(null)
  const [all,      setAll]      = useState<ForecastAllResponse | null>(null)
  const [metrics,  setMetrics]  = useState<ForecastMetrics | null>(null)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')

  const load = async () => {
    setLoading(true); setError('')
    try {
      const [m] = await Promise.all([api.forecastMetrics()])
      setMetrics(m)
      if (tab === 'Single Model') {
        const d = await api.forecast(horizon, model)
        setSingle(d)
      } else {
        const d = await api.forecastAll(horizon)
        setAll(d)
      }
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [tab, horizon, model])

  const singleChartData = single?.forecast.map(p => ({
    date: p.date.slice(5),
    Forecast: +p.forecast.toFixed(1),
    Upper: +p.upper_bound.toFixed(1),
    Lower: +p.lower_bound.toFixed(1),
  })) || []

  const allChartData = (() => {
    if (!all?.forecasts) return []
    const dates = Object.values(all.forecasts)[0]?.map(p => p.date.slice(5)) || []
    return dates.map((date, i) => {
      const row: Record<string, any> = { date }
      Object.entries(all.forecasts).forEach(([m, pts]) => { row[m] = +(pts[i]?.forecast || 0).toFixed(1) })
      return row
    })
  })()

  return (
    <div>
      <SectionHeader title="Demand Forecast" subtitle="3-model ensemble: ARIMA · Prophet · N-BEATS" />

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <TabBar tabs={['Single Model', 'Compare All']} active={tab} onChange={setTab} />
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted">Horizon:</span>
          {[7, 14, 30, 60, 90].map(h => (
            <button key={h} onClick={() => setHorizon(h)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                horizon === h ? 'bg-accent text-white' : 'bg-surface2 text-muted hover:text-text border border-border'
              }`}>{h}d</button>
          ))}
        </div>
        {tab === 'Single Model' && (
          <select value={model} onChange={e => setModel(e.target.value)}
            className="bg-surface2 border border-border text-sm text-text rounded-lg px-3 py-1.5 outline-none">
            <option value="best">Auto (Best)</option>
            <option value="Prophet">Prophet</option>
            <option value="N-BEATS">N-BEATS</option>
            <option value="ARIMA">ARIMA</option>
          </select>
        )}
      </div>

      {loading ? <Spinner /> : error ? <ErrorState message={error} /> : (
        <>
          {/* Single model view */}
          {tab === 'Single Model' && single && (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6 stagger">
                <StatCard label="Model Used"    value={single.model_used}  icon={<Zap size={14} />}         accent="#3B82F6" />
                <StatCard label="Total Units"   value={(single.business_summary.total_forecast_units || 0).toLocaleString(undefined,{maximumFractionDigits:0})} icon={<TrendingUp size={14} />} accent="#10B981" />
                <StatCard label="Daily Average" value={(single.business_summary.avg_daily_demand || 0).toFixed(0)} icon={<Target size={14} />} accent="#F59E0B" />
                <StatCard label="Peak Day"      value={single.business_summary.peak_day || '—'} icon={<Clock size={14} />} accent="#8B5CF6" />
              </div>

              <div className="card p-5">
                <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">
                  {horizon}-day demand forecast — {single.model_used}
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={singleChartData}>
                    <defs>
                      <linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#3B82F6" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="cig" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#3B82F6" stopOpacity={0.08} />
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="date" tick={{ fill:'#64748B', fontSize:11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill:'#64748B', fontSize:11 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="Upper" stroke="none" fill="url(#cig)" name="Upper" />
                    <Area type="monotone" dataKey="Forecast" stroke="#3B82F6" strokeWidth={2.5} fill="url(#fg)" name="Forecast" />
                    <Area type="monotone" dataKey="Lower" stroke="none" fill="url(#cig)" name="Lower" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </>
          )}

          {/* Compare all models */}
          {tab === 'Compare All' && all && (
            <>
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs text-muted">Best model:</span>
                <span className="badge badge-info">{all.best_model}</span>
              </div>
              <div className="card p-5 mb-4">
                <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">All models — {horizon}-day forecast</div>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={allChartData}>
                    <XAxis dataKey="date" tick={{ fill:'#64748B', fontSize:11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill:'#64748B', fontSize:11 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize:12, color:'#64748B' }} />
                    {Object.keys(all.forecasts).map(m => (
                      <Line key={m} type="monotone" dataKey={m} stroke={MODEL_COLORS[m] || '#888'} strokeWidth={2} dot={false} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          )}

          {/* Metrics table */}
          {metrics && (
            <div className="card p-5">
              <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">Model evaluation — 30-day holdout</div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-muted text-xs uppercase tracking-wider border-b border-border">
                      <th className="text-left pb-3">Model</th>
                      <th className="text-right pb-3">MAE</th>
                      <th className="text-right pb-3">RMSE</th>
                      <th className="text-right pb-3">MAPE</th>
                      <th className="text-right pb-3">Fit Time</th>
                      <th className="text-right pb-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {Object.entries(metrics.models).map(([name, m]) => (
                      <tr key={name} className="hover:bg-surface2/50 transition-colors">
                        <td className="py-3 font-medium" style={{ color: MODEL_COLORS[name] || '#E2E8F0' }}>{name}</td>
                        <td className="py-3 text-right font-mono text-xs text-muted">{m.MAE?.toFixed(2)}</td>
                        <td className="py-3 text-right font-mono text-xs text-muted">{m.RMSE?.toFixed(2)}</td>
                        <td className="py-3 text-right font-mono text-xs text-muted">{m.MAPE?.toFixed(2)}%</td>
                        <td className="py-3 text-right font-mono text-xs text-muted">{m.fit_time_s?.toFixed(1)}s</td>
                        <td className="py-3 text-right">
                          {name === metrics.best_model
                            ? <span className="badge badge-low">✓ Best</span>
                            : <span className="text-muted text-xs">—</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}