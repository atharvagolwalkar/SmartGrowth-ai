'use client'
import clsx from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

// ── Stat Card ─────────────────────────────────────────────────────────────────
interface StatCardProps {
  label: string
  value: string | number
  delta?: string
  deltaType?: 'up' | 'down' | 'neutral'
  icon?: React.ReactNode
  accent?: string
  delay?: number
}

export function StatCard({ label, value, delta, deltaType = 'neutral', icon, accent = '#3B82F6', delay = 0 }: StatCardProps) {
  return (
    <div
      className="card p-5 animate-fade-up"
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards', opacity: 0 }}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-xs text-muted uppercase tracking-widest font-medium">{label}</span>
        {icon && (
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
               style={{ background: `${accent}18`, color: accent }}>
            {icon}
          </div>
        )}
      </div>
      <div className="text-2xl font-bold tracking-tight mb-1" style={{ color: '#E2E8F0' }}>{value}</div>
      {delta && (
        <div className={clsx('flex items-center gap-1 text-xs font-medium',
          deltaType === 'up'   ? 'text-emerald-400' :
          deltaType === 'down' ? 'text-red-400' : 'text-muted'
        )}>
          {deltaType === 'up'   ? <TrendingUp size={11} /> :
           deltaType === 'down' ? <TrendingDown size={11} /> : <Minus size={11} />}
          {delta}
        </div>
      )}
    </div>
  )
}

// ── Section Header ─────────────────────────────────────────────────────────────
export function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-3 mb-1">
        <div className="w-0.5 h-5 bg-accent rounded-full" />
        <h2 className="text-lg font-bold tracking-tight">{title}</h2>
      </div>
      {subtitle && <p className="text-sm text-muted ml-3.5 pl-0.5">{subtitle}</p>}
    </div>
  )
}

// ── Risk Badge ─────────────────────────────────────────────────────────────────
export function RiskBadge({ level }: { level: string }) {
  return (
    <span className={clsx('badge', {
      'badge-high':   level === 'High',
      'badge-medium': level === 'Medium',
      'badge-low':    level === 'Low',
      'badge-info':   !['High','Medium','Low'].includes(level),
    })}>
      {level}
    </span>
  )
}

// ── Risk Bar ───────────────────────────────────────────────────────────────────
export function RiskBar({ value, max = 1 }: { value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100)
  const color = pct > 70 ? '#EF4444' : pct > 40 ? '#F59E0B' : '#10B981'
  return (
    <div className="w-full bg-surface2 rounded-full h-1.5 overflow-hidden">
      <div className="h-full rounded-full transition-all duration-700"
           style={{ width: `${pct}%`, background: color }} />
    </div>
  )
}

// ── Loading Spinner ────────────────────────────────────────────────────────────
export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="rounded-full border-2 border-border border-t-accent animate-spin"
           style={{ width: size, height: size }} />
    </div>
  )
}

// ── Error State ────────────────────────────────────────────────────────────────
export function ErrorState({ message }: { message: string }) {
  return (
    <div className="card p-6 border-red-900/40 bg-red-950/10 text-red-400 text-sm">
      <div className="font-semibold mb-1">Error</div>
      <div className="text-red-400/70">{message}</div>
    </div>
  )
}

// ── Empty State ────────────────────────────────────────────────────────────────
export function EmptyState({ message, icon }: { message: string; icon?: string }) {
  return (
    <div className="card p-12 text-center">
      <div className="text-3xl mb-3">{icon || '📭'}</div>
      <div className="text-muted text-sm">{message}</div>
    </div>
  )
}

// ── Data Row ───────────────────────────────────────────────────────────────────
export function DataRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-border last:border-0 text-sm">
      <span className="text-muted">{label}</span>
      <span className="font-mono font-medium text-text">{value}</span>
    </div>
  )
}

// ── Tab Bar ────────────────────────────────────────────────────────────────────
export function TabBar({ tabs, active, onChange }: {
  tabs: string[]; active: string; onChange: (t: string) => void
}) {
  return (
    <div className="flex gap-1 bg-surface2 p-1 rounded-lg border border-border w-fit">
      {tabs.map(tab => (
        <button key={tab} onClick={() => onChange(tab)}
          className={clsx(
            'px-4 py-1.5 rounded-md text-sm font-medium transition-all',
            active === tab ? 'bg-accent text-white' : 'text-muted hover:text-text'
          )}>
          {tab}
        </button>
      ))}
    </div>
  )
}