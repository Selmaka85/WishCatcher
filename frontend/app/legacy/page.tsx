'use client'

import { useState } from 'react'
import Dashboard from '@/components/Dashboard'
import Filters from '@/components/Filters'
import ProductGaps from '@/components/ProductGaps'
import { QueryClient, QueryClientProvider } from 'react-query'

const queryClient = new QueryClient()

type Tab = 'wishcatcher' | 'product-gaps'

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>('wishcatcher')
  const [filters, setFilters] = useState({
    geography: { level: 'global' },
    language: 'all',
    domain: 'all',
  })

  return (
    <QueryClientProvider client={queryClient}>
      <main className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <header className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              WishCatcher + Astra Genesis
            </h1>
            <p className="text-gray-600">
              Sistem complet pentru detectare dorințe și generare business plans
            </p>
          </header>

          {/* Tabs */}
          <div className="mb-6 border-b border-gray-200">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('wishcatcher')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'wishcatcher'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                WishCatcher
              </button>
              <button
                onClick={() => setActiveTab('product-gaps')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'product-gaps'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Product Gap Finder
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'wishcatcher' && (
            <>
              <Filters filters={filters} setFilters={setFilters} />
              <Dashboard filters={filters} />
            </>
          )}

          {activeTab === 'product-gaps' && <ProductGaps />}
        </div>
      </main>
    </QueryClientProvider>
  )
}
