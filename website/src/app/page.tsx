'use client'
import { useEffect, useState } from 'react'
import Sidebar from '@/components/Sidebar'
import Overview from '@/components/Overview'
import Forecast from '@/components/Forecast'
import NLPInsights from '@/components/NLPInsights'
import { CustomerAnalysis, HighRisk, BatchPredict } from '@/components/Pages'
import { api } from '@/lib/api'

export default function Home() {
  const [page,      setPage]      = useState('overview')
  const [apiOnline, setApiOnline] = useState(false)

  useEffect(() => {
    api.health()
      .then(() => setApiOnline(true))
      .catch(() => setApiOnline(false))
  }, [])

  const renderPage = () => {
    switch (page) {
      case 'overview':  return <Overview />
      case 'customers': return <CustomerAnalysis />
      case 'forecast':  return <Forecast />
      case 'nlp':       return <NLPInsights />
      case 'highrisk':  return <HighRisk />
      case 'batch':     return <BatchPredict />
      default:          return <Overview />
    }
  }

  return (
    <div className="min-h-screen bg-bg flex">
      <Sidebar active={page} onChange={setPage} apiOnline={apiOnline} />

      {/* Main content */}
      <main className="flex-1 min-h-screen overflow-x-hidden">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-6">
          {/* Top bar */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="text-xs text-muted uppercase tracking-widest mb-1">
                {new Date().toLocaleDateString('en-US', { weekday:'long', year:'numeric', month:'long', day:'numeric' })}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${apiOnline ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`} />
              <span className="text-xs text-muted font-mono">
                {apiOnline ? 'Connected' : 'Offline'}
              </span>
            </div>
          </div>

          {/* Page content */}
          <div key={page} className="animate-fade-in">
            {renderPage()}
          </div>
        </div>
      </main>
    </div>
  )
}