'use client'
import { useEffect, useState } from 'react'
import { LayoutDashboard, Users, TrendingUp, MessageSquare, AlertTriangle, Layers, Menu, X, Activity, Zap } from 'lucide-react'
import clsx from 'clsx'

const NAV = [
  { id: 'overview',  label: 'Overview',          icon: LayoutDashboard },
  { id: 'customers', label: 'Customer Analysis',  icon: Users },
  { id: 'forecast',  label: 'Demand Forecast',    icon: TrendingUp },
  { id: 'nlp',       label: 'NLP Insights',       icon: MessageSquare },
  { id: 'highrisk',  label: 'High Risk',           icon: AlertTriangle },
  { id: 'batch',     label: 'Batch Predict',       icon: Layers },
]

interface Props {
  active: string
  onChange: (id: string) => void
  apiOnline: boolean
}

export default function Sidebar({ active, onChange, apiOnline }: Props) {
  const [open, setOpen] = useState(false)
  const [isDesktop, setIsDesktop] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia('(min-width: 768px)')

    const syncLayout = (matches: boolean) => {
      setIsDesktop(matches)
      setOpen(matches)
    }

    syncLayout(mediaQuery.matches)

    const handleMediaChange = (event: MediaQueryListEvent) => {
      syncLayout(event.matches)
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false)
      }
    }

    mediaQuery.addEventListener('change', handleMediaChange)
    window.addEventListener('keydown', handleKeyDown)

    return () => {
      mediaQuery.removeEventListener('change', handleMediaChange)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  useEffect(() => {
    document.body.style.overflow = open && !isDesktop ? 'hidden' : ''

    return () => {
      document.body.style.overflow = ''
    }
  }, [isDesktop, open])

  return (
    <>
      {/* Mobile toggle */}
      <button
        type="button"
        aria-label={open ? 'Close navigation menu' : 'Open navigation menu'}
        aria-expanded={open}
        aria-controls="app-sidebar"
        onClick={() => setOpen((current) => !current)}
        className="fixed top-4 left-4 z-50 bg-surface border border-border rounded-lg p-2"
      >
        {open ? <X size={18} /> : <Menu size={18} />}
      </button>

      {/* Backdrop */}
      {open && (
        <div className="fixed inset-0 z-30 bg-black/60 md:hidden" onClick={() => setOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        id="app-sidebar"
        className={clsx(
          'fixed left-0 top-0 h-full z-40 w-60 bg-surface border-r border-border',
          'flex flex-col transition-transform duration-300',
          open ? 'translate-x-0 pointer-events-auto' : '-translate-x-full pointer-events-none'
        )}
      >

        {/* Logo */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
              <Zap size={14} className="text-white" />
            </div>
            <div>
              <div className="font-bold text-sm tracking-tight">SmartGrowth AI</div>
              <div className="text-[10px] text-muted uppercase tracking-widest">Intelligence Platform</div>
            </div>
          </div>

          {/* API status */}
          <div className={clsx(
            'mt-4 flex items-center gap-2 px-3 py-2 rounded-lg text-xs',
            apiOnline ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/50'
                      : 'bg-red-950/40 text-red-400 border border-red-900/50'
          )}>
            <Activity size={10} className={apiOnline ? 'text-emerald-400' : 'text-red-400'} />
            <span className={clsx('w-1.5 h-1.5 rounded-full', apiOnline ? 'bg-emerald-400 animate-pulse' : 'bg-red-400')} />
            {apiOnline ? 'API Online' : 'API Offline'}
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          <div className="text-[10px] text-muted uppercase tracking-widest px-3 py-2">Navigation</div>
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => { onChange(id); setOpen(false) }}
              className={clsx(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all',
                active === id
                  ? 'bg-accent/10 text-accent border border-accent/20 font-medium'
                  : 'text-muted hover:text-text hover:bg-surface2'
              )}
            >
              <Icon size={15} />
              {label}
              {id === 'highrisk' && (
                <span className="ml-auto w-1.5 h-1.5 rounded-full bg-danger animate-pulse" />
              )}
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border">
          <div className="text-[10px] text-muted leading-relaxed">
            <div className="font-mono">v2.0.0</div>
            <div>Prophet · N-BEATS · ChromaDB</div>
            <div>Telco + Synthetic Data</div>
          </div>
        </div>
      </aside>
    </>
  )
}
