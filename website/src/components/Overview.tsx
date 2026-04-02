'use client'
import { useEffect, useState } from 'react'
import { Users, TrendingDown, DollarSign, Clock, Wifi, AlertTriangle } from 'lucide-react'
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { api, Customer } from '@/lib/api'
import { StatCard, SectionHeader, Spinner, ErrorState } from '@/components/UI'

const CHART_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface2 border border-border rounded-lg px-3 py-2 text-xs">
      <div className="text-muted mb-1">{label}</div>
      {payload.map((p: any, i: number) => (
        <div key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}</div>
      ))}
    </div>
  )
}

export default function Overview() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.customers(500)
      .then(d => setCustomers(d.customers || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />
  if (error)   return <ErrorState message={error} />

  // ── Derived stats ──────────────────────────────────────────────────────────
  const total       = customers.length
  const churned     = customers.filter(c => c.churn).length
  const churnRate   = total ? ((churned / total) * 100) : 0
  const avgCharges  = customers.reduce((s, c) => s + (c.monthly_charges || 0), 0) / (total || 1)
  const avgTenure   = customers.reduce((s, c) => s + (c.tenure || 0), 0) / (total || 1)
  const revAtRisk   = customers.filter(c => c.churn).reduce((s, c) => s + (c.monthly_charges || 0), 0)

  // Churn by contract
  const contractMap: Record<string, { total: number; churned: number }> = {}
  customers.forEach(c => {
    const k = c.contract || 'Unknown'
    if (!contractMap[k]) contractMap[k] = { total: 0, churned: 0 }
    contractMap[k].total++
    if (c.churn) contractMap[k].churned++
  })
  const contractData = Object.entries(contractMap).map(([name, v]) => ({
    name, churnRate: v.total ? +(v.churned / v.total * 100).toFixed(1) : 0, count: v.total,
  }))

  // Internet service distribution
  const serviceMap: Record<string, number> = {}
  customers.forEach(c => { const k = c.internet_service || 'Unknown'; serviceMap[k] = (serviceMap[k] || 0) + 1 })
  const serviceData = Object.entries(serviceMap).map(([name, value]) => ({ name, value }))

  // Tenure histogram buckets
  const buckets = [
    { name: '0-12m', total: 0, churned: 0 },
    { name: '13-24m', total: 0, churned: 0 },
    { name: '25-48m', total: 0, churned: 0 },
    { name: '49-60m', total: 0, churned: 0 },
    { name: '60m+', total: 0, churned: 0 },
  ]
  customers.forEach(c => {
    const t = c.tenure || 0
    const i = t <= 12 ? 0 : t <= 24 ? 1 : t <= 48 ? 2 : t <= 60 ? 3 : 4
    buckets[i].total++
    if (c.churn) buckets[i].churned++
  })

  // Monthly charges distribution
  const chargeBuckets = [
    { name: '<$30', count: 0 }, { name: '$30-50', count: 0 },
    { name: '$50-70', count: 0 }, { name: '$70-90', count: 0 }, { name: '>$90', count: 0 }
  ]
  customers.forEach(c => {
    const m = c.monthly_charges || 0
    const i = m < 30 ? 0 : m < 50 ? 1 : m < 70 ? 2 : m < 90 ? 3 : 4
    chargeBuckets[i].count++
  })

  return (
    <div>
      <SectionHeader title="Overview" subtitle={`Live data from ${total.toLocaleString()} customers`} />

      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 mb-8 stagger">
        <StatCard label="Total Customers"   value={total.toLocaleString()}     icon={<Users size={14} />}        accent="#3B82F6" delay={0} />
        <StatCard label="Churn Rate"        value={`${churnRate.toFixed(1)}%`} icon={<TrendingDown size={14} />} accent="#EF4444" delta={churnRate > 20 ? 'Above 20% baseline' : 'Below 20% baseline'} deltaType={churnRate > 20 ? 'down' : 'up'} delay={50} />
        <StatCard label="Avg Monthly"       value={`$${avgCharges.toFixed(0)}`} icon={<DollarSign size={14} />}  accent="#10B981" delay={100} />
        <StatCard label="Avg Tenure"        value={`${avgTenure.toFixed(0)} mo`} icon={<Clock size={14} />}      accent="#F59E0B" delay={150} />
        <StatCard label="Churned Customers" value={churned.toLocaleString()}    icon={<AlertTriangle size={14} />} accent="#EF4444" delay={200} />
        <StatCard label="Revenue at Risk"   value={`$${revAtRisk.toLocaleString(undefined,{maximumFractionDigits:0})}`} icon={<DollarSign size={14} />} accent="#F59E0B" delta="Monthly" deltaType="neutral" delay={250} />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">

        {/* Churn by contract */}
        <div className="card p-5 lg:col-span-2">
          <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">Churn rate by contract</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={contractData} barCategoryGap="35%">
              <XAxis dataKey="name" tick={{ fill: '#64748B', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748B', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar dataKey="churnRate" name="Churn %" radius={[4,4,0,0]}>
                {contractData.map((_, i) => (
                  <Cell key={i} fill={_.churnRate > 40 ? '#EF4444' : _.churnRate > 15 ? '#F59E0B' : '#10B981'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Internet service donut */}
        <div className="card p-5">
          <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">Internet service</div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={serviceData} dataKey="value" cx="50%" cy="50%" innerRadius={50} outerRadius={75} paddingAngle={3}>
                {serviceData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-3">
            {serviceData.map((d, i) => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                  <span className="text-muted">{d.name}</span>
                </div>
                <span className="font-mono text-text">{d.value.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Tenure vs churn */}
        <div className="card p-5">
          <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">Tenure distribution vs churn</div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={buckets} barCategoryGap="25%">
              <XAxis dataKey="name" tick={{ fill: '#64748B', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748B', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar dataKey="total"   name="Total"   fill="#3B82F620" radius={[4,4,0,0]} />
              <Bar dataKey="churned" name="Churned" fill="#EF4444"   radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Monthly charges distribution */}
        <div className="card p-5">
          <div className="text-sm font-semibold mb-4 text-muted uppercase tracking-wider">Monthly charges distribution</div>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={chargeBuckets}>
              <defs>
                <linearGradient id="chargeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#3B82F6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="name" tick={{ fill: '#64748B', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748B', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="count" name="Customers" stroke="#3B82F6" strokeWidth={2} fill="url(#chargeGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}