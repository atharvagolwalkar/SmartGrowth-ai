'use client'
import { useEffect, useState } from 'react'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { api, NLPSearchResult, NLPTimelinePoint } from '@/lib/api'
import { StatCard, SectionHeader, Spinner, ErrorState, TabBar } from '@/components/UI'
import { Search, MessageSquare, TrendingUp, TrendingDown, Minus } from 'lucide-react'

const SUGGESTIONS = ['billing problem', 'slow internet', 'great support', 'cancel service', 'refund request']

const SentimentDot = ({ label }: { label?: string }) => {
  const color = label === 'positive' ? '#10B981' : label === 'negative' ? '#EF4444' : '#64748B'
  return <span className="inline-flex items-center gap-1 text-xs" style={{ color }}>● {label}</span>
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface2 border border-border rounded-lg px-3 py-2 text-xs space-y-1">
      <div className="text-muted">{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} style={{ color: p.color }}>{p.name}: {Number(p.value).toFixed(1)}{p.name.includes('pct') ? '%' : ''}</div>
      ))}
    </div>
  )
}

export default function NLPInsights() {
  const [tab,      setTab]      = useState('Search')
  const [query,    setQuery]    = useState('')
  const [results,  setResults]  = useState<NLPSearchResult[]>([])
  const [timeline, setTimeline] = useState<NLPTimelinePoint[]>([])
  const [summary,  setSummary]  = useState<any>(null)
  const [stats,    setStats]    = useState<any>(null)
  const [loading,  setLoading]  = useState(false)
  const [tlLoading,setTlLoading]= useState(true)
  const [error,    setError]    = useState('')

  useEffect(() => {
    Promise.all([api.nlpTimeline('W'), api.nlpSummary(), api.nlpStats()])
      .then(([tl, sm, st]) => { setTimeline(tl.timeline); setSummary(sm); setStats(st) })
      .catch(e => setError(e.message))
      .finally(() => setTlLoading(false))
  }, [])

  const doSearch = async (q: string) => {
    if (!q.trim()) return
    setQuery(q); setLoading(true); setError('')
    try {
      const d = await api.nlpSearch(q, 8)
      setResults(d.results)
    } catch (e: any) { setError(e.message) }
    finally { setLoading(false) }
  }

  const trendInfo = stats?.trend
  const TrendIcon = trendInfo?.direction === 'improving' ? TrendingUp :
                    trendInfo?.direction === 'worsening' ? TrendingDown : Minus

  return (
    <div>
      <SectionHeader title="NLP Insights" subtitle="Semantic search · Sentiment analysis · Feedback intelligence" />

      {/* KPI row */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6 stagger">
          <StatCard label="Total Feedback" value={(stats.total_feedback || 0).toLocaleString()} icon={<MessageSquare size={14} />} accent="#3B82F6" />
          <StatCard label="Positive" value={`${(stats.sentiment_distribution?.positive || 0).toFixed(1)}%`} accent="#10B981" deltaType="up" />
          <StatCard label="Negative" value={`${(stats.sentiment_distribution?.negative || 0).toFixed(1)}%`} accent="#EF4444" deltaType="down" />
          <StatCard label="Search Backend" value={(stats.index_stats?.backend || '—').toUpperCase()} accent="#8B5CF6" />
        </div>
      )}

      {/* Trend banner */}
      {trendInfo && (
        <div className={`card p-3 mb-6 flex items-center gap-3 border-l-2 ${
          trendInfo.direction === 'improving' ? 'border-l-emerald-500' :
          trendInfo.direction === 'worsening' ? 'border-l-red-500' : 'border-l-muted'
        }`}>
          <TrendIcon size={16} className={
            trendInfo.direction === 'improving' ? 'text-emerald-400' :
            trendInfo.direction === 'worsening' ? 'text-red-400' : 'text-muted'
          } />
          <span className="text-sm">{trendInfo.summary}</span>
        </div>
      )}

      <TabBar tabs={['Search', 'Timeline', 'Breakdown']} active={tab} onChange={setTab} />
      <div className="mt-6">

        {/* ── SEARCH ── */}
        {tab === 'Search' && (
          <div>
            <div className="card p-4 mb-4">
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                  <input
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && doSearch(query)}
                    placeholder="Search by meaning — e.g. billing problem, slow internet..."
                    className="w-full bg-surface2 border border-border rounded-lg pl-9 pr-4 py-2.5 text-sm text-text placeholder:text-muted outline-none focus:border-accent transition-colors"
                  />
                </div>
                <button onClick={() => doSearch(query)}
                  className="px-4 py-2.5 bg-accent hover:bg-accent/80 text-white rounded-lg text-sm font-medium transition-colors">
                  Search
                </button>
              </div>
              <div className="flex flex-wrap gap-2 mt-3">
                <span className="text-xs text-muted">Try:</span>
                {SUGGESTIONS.map(s => (
                  <button key={s} onClick={() => doSearch(s)}
                    className="text-xs px-2.5 py-1 bg-surface2 hover:bg-accent/10 hover:text-accent border border-border hover:border-accent/30 rounded-full transition-all text-muted">
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {loading ? <Spinner /> : error ? <ErrorState message={error} /> : (
              <div className="space-y-2">
                {results.length === 0 && query && (
                  <div className="card p-8 text-center text-muted text-sm">No results found — try a different query.</div>
                )}
                {results.map((r, i) => (
                  <div key={r.feedback_id} className="card p-4 hover:border-accent/30 transition-all animate-fade-up"
                       style={{ animationDelay: `${i * 40}ms`, animationFillMode: 'forwards', opacity: 0 }}>
                    <div className="flex items-start justify-between gap-4 mb-2">
                      <p className="text-sm leading-relaxed flex-1">{r.feedback_text}</p>
                      <div className="text-right shrink-0">
                        <div className="text-lg font-bold font-mono" style={{ color: '#3B82F6' }}>
                          {(r.similarity_score * 100).toFixed(0)}%
                        </div>
                        <div className="text-[10px] text-muted">match</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 flex-wrap">
                      <SentimentDot label={r.sentiment_label} />
                      {r.category && <span className="text-xs text-muted">{r.category.replace(/_/g,' ')}</span>}
                      {r.channel   && <span className="text-xs text-muted">{r.channel}</span>}
                      {r.customer_id && <span className="text-xs font-mono text-muted">{r.customer_id}</span>}
                    </div>
                    <div className="mt-2.5 h-1 bg-surface2 rounded-full overflow-hidden">
                      <div className="h-full bg-accent/50 rounded-full" style={{ width: `${r.similarity_score*100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── TIMELINE ── */}
        {tab === 'Timeline' && (
          tlLoading ? <Spinner /> : (
            <div className="space-y-4">
              <div className="card p-5">
                <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">Weekly sentiment trend</div>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={timeline}>
                    <defs>
                      <linearGradient id="pg" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#10B981" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="ng" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor="#EF4444" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="period_str" tick={{ fill:'#64748B', fontSize:10 }} axisLine={false} tickLine={false} interval={3} />
                    <YAxis tick={{ fill:'#64748B', fontSize:10 }} axisLine={false} tickLine={false} tickFormatter={v=>`${v}%`} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="positive_pct" name="Positive %" stroke="#10B981" strokeWidth={2} fill="url(#pg)" />
                    <Area type="monotone" dataKey="negative_pct" name="Negative %" stroke="#EF4444" strokeWidth={2} fill="url(#ng)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="card p-5">
                <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">Feedback volume</div>
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={timeline}>
                    <XAxis dataKey="period_str" tick={{ fill:'#64748B', fontSize:10 }} axisLine={false} tickLine={false} interval={3} />
                    <YAxis tick={{ fill:'#64748B', fontSize:10 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="total_count" name="Tickets" fill="#3B82F6" opacity={0.6} radius={[3,3,0,0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )
        )}

        {/* ── BREAKDOWN ── */}
        {tab === 'Breakdown' && (
          tlLoading ? <Spinner /> : !summary ? <ErrorState message="No summary data" /> : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="card p-5">
                <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">Sentiment by category</div>
                <div className="space-y-3">
                  {Object.entries(summary.by_category || {}).map(([cat, dist]: [string, any]) => {
                    const pos = dist.positive || 0
                    const neg = dist.negative || 0
                    const neu = 100 - pos - neg
                    return (
                      <div key={cat}>
                        <div className="flex justify-between text-xs mb-1.5">
                          <span className="text-muted capitalize">{cat.replace(/_/g,' ')}</span>
                          <span className="font-mono"><span className="text-emerald-400">+{pos.toFixed(0)}%</span> <span className="text-red-400">{neg.toFixed(0)}%</span></span>
                        </div>
                        <div className="flex h-1.5 rounded-full overflow-hidden gap-px">
                          <div style={{ width:`${pos}%`, background:'#10B981' }} />
                          <div style={{ width:`${neu}%`, background:'#1E2D45' }} />
                          <div style={{ width:`${neg}%`, background:'#EF4444' }} />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
              <div className="card p-5">
                <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">Negative rate by channel</div>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={Object.entries(summary.by_channel || {}).map(([ch, dist]: [string, any]) => ({
                    name: ch, negative: +(dist.negative || 0).toFixed(1)
                  }))} layout="vertical">
                    <XAxis type="number" tick={{ fill:'#64748B', fontSize:11 }} axisLine={false} tickLine={false} tickFormatter={v=>`${v}%`} />
                    <YAxis type="category" dataKey="name" tick={{ fill:'#64748B', fontSize:11 }} axisLine={false} tickLine={false} width={70} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="negative" name="Negative %" radius={[0,4,4,0]}>
                      {Object.entries(summary.by_channel || {}).map(([, dist]: [string, any], i) => (
                        <rect key={i} fill={(dist.negative||0) > 50 ? '#EF4444' : (dist.negative||0) > 30 ? '#F59E0B' : '#10B981'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  )
}
