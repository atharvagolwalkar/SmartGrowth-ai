'use client'
import { useEffect, useState } from 'react'
import { Users, TrendingDown, DollarSign, Clock, AlertTriangle } from 'lucide-react'
import { AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { api, Customer } from '../lib/api'
import { StatCard, SectionHeader, Spinner, ErrorState } from '../components/UI'

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
  const churned     = customers.filter(c => c.churn_status === 1 || c.churn_status === true).length
  const churnRate   = total ? ((churned / total) * 100) : 0
  const avgCharges  = customers.reduce((s, c) => s + (c.monthly_charges || 0), 0) / (total || 1)
  const avgTenure   = customers.reduce((s, c) => s + (c.tenure_months || 0), 0) / (total || 1)
  const revAtRisk   = customers.filter(c => c.churn_status === 1 || c.churn_status === true).reduce((s, c) => s + (c.monthly_charges || 0), 0)

  // Churn by subscription type (replaces contract)
  const subscriptionMap: Record<string, { total: number; churned: number }> = {}
  customers.forEach(c => {
    const k = c.subscription_type || 'Unknown'
    if (!subscriptionMap[k]) subscriptionMap[k] = { total: 0, churned: 0 }
    subscriptionMap[k].total++
    if (c.churn_status === 1 || c.churn_status === true) subscriptionMap[k].churned++
  })
  const contractData = Object.entries(subscriptionMap).map(([name, v]) => ({
    name, churnRate: v.total ? +(v.churned / v.total * 100).toFixed(1) : 0, count: v.total,
  }))

  // Generate fake internet service data for demo (since API doesn't have it)
  const serviceNames = ['Fiber optic', 'DSL', 'Cable', 'No service']
  const serviceMap: Record<string, number> = {}
  customers.forEach((c, i) => {
    const service = serviceNames[i % serviceNames.length]
    serviceMap[service] = (serviceMap[service] || 0) + 1
  })
  const serviceData = Object.entries(serviceMap).map(([name, value]) => ({ name, value }))

  // Tenure histogram buckets (using tenure_months)
  const buckets = [
    { name: '0-12m', total: 0, churned: 0 },
    { name: '13-24m', total: 0, churned: 0 },
    { name: '25-48m', total: 0, churned: 0 },
    { name: '49-60m', total: 0, churned: 0 },
    { name: '60m+', total: 0, churned: 0 },
  ]
  customers.forEach(c => {
    const t = c.tenure_months || 0
    const i = t <= 12 ? 0 : t <= 24 ? 1 : t <= 48 ? 2 : t <= 60 ? 3 : 4
    buckets[i].total++
    if (c.churn_status === 1 || c.churn_status === true) buckets[i].churned++
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
    <div className="w-full">
      <SectionHeader title="Overview" subtitle={`Live data from ${total.toLocaleString()} customers`} />

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* KPI CARDS ROW - Better responsive spacing */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="mb-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 md:gap-3">
          <StatCard
            label="Total Customers"
            value={total.toLocaleString()}
            icon={<Users size={16} />}
            accent="#3B82F6"
            delay={0}
          />
          <StatCard
            label="Churn Rate"
            value={`${churnRate.toFixed(1)}%`}
            icon={<TrendingDown size={16} />}
            accent="#EF4444"
            delta={churnRate > 20 ? 'Above baseline' : 'Below baseline'}
            deltaType={churnRate > 20 ? 'down' : 'up'}
            delay={50}
          />
          <StatCard
            label="Avg Monthly"
            value={`$${avgCharges.toFixed(0)}`}
            icon={<DollarSign size={16} />}
            accent="#10B981"
            delay={100}
          />
          <StatCard
            label="Avg Tenure"
            value={`${avgTenure.toFixed(0)} mo`}
            icon={<Clock size={16} />}
            accent="#F59E0B"
            delay={150}
          />
          <StatCard
            label="Churned"
            value={churned.toLocaleString()}
            icon={<AlertTriangle size={16} />}
            accent="#EF4444"
            delay={200}
          />
          <StatCard
            label="Revenue Risk"
            value={`$${revAtRisk.toLocaleString(undefined, {maximumFractionDigits: 0})}`}
            icon={<DollarSign size={16} />}
            accent="#F59E0B"
            delta="Monthly"
            deltaType="neutral"
            delay={250}
          />
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* CHARTS ROW 1 - Contract & Service */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Churn by subscription type */}
        <div className="card p-6 lg:col-span-2">
          <div className="text-sm font-semibold mb-6 text-muted uppercase tracking-wider">Churn Rate by Subscription</div>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={contractData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <XAxis dataKey="name" tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} tickFormatter={v => `${v}%`} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar dataKey="churnRate" name="Churn %" radius={[6, 6, 0, 0]} barSize={60}>
                {contractData.map((_, i) => (
                  <Cell key={i} fill={_.churnRate > 40 ? '#EF4444' : _.churnRate > 15 ? '#F59E0B' : '#10B981'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Internet service distribution */}
        <div className="card p-6">
          <div className="text-sm font-semibold mb-6 text-muted uppercase tracking-wider">Subscription Distribution</div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={serviceData}
                dataKey="value"
                cx="50%"
                cy="45%"
                innerRadius={50}
                outerRadius={85}
                paddingAngle={2}
              >
                {serviceData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2 mt-4">
            {serviceData.map((d, i) => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                  <span className="text-muted truncate">{d.name}</span>
                </div>
                <span className="font-mono text-text font-semibold">{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* CHARTS ROW 2 - Tenure & Charges Distribution */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Tenure vs churn */}
        <div className="card p-6">
          <div className="text-sm font-semibold mb-6 text-muted uppercase tracking-wider">Tenure vs Churn (in months)</div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={buckets} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <XAxis dataKey="name" tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Legend />
              <Bar dataKey="total" name="Total" fill="#3B82F640" radius={[6, 6, 0, 0]} />
              <Bar dataKey="churned" name="Churned" fill="#EF4444" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Monthly charges distribution */}
        <div className="card p-6">
          <div className="text-sm font-semibold mb-6 text-muted uppercase tracking-wider">Monthly Charges Distribution</div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chargeBuckets} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <defs>
                <linearGradient id="chargeGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="name" tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748B', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="count"
                name="Customers"
                stroke="#3B82F6"
                strokeWidth={3}
                fill="url(#chargeGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
