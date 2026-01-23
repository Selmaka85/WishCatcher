'use client'

import { wishesApi, WishData } from '@/lib/api'
import WishCard from './WishCard'
import { useState } from 'react'

interface DashboardProps {
  filters: any
}

export default function Dashboard({ filters }: DashboardProps) {
  const [sources, setSources] = useState<string[]>(['reddit'])
  const [limit, setLimit] = useState(50)
  const [isCollecting, setIsCollecting] = useState(false)

  const [wishesData, setWishesData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  const handleCollect = async () => {
    setIsCollecting(true)
    setIsLoading(true)
    setError(null)
    
    try {
      // Validare: sources nu poate fi gol
      if (!sources || sources.length === 0) {
        throw new Error('Trebuie să selectezi cel puțin o sursă')
      }
      
      const result = await wishesApi.collect(sources, filters, limit)
      setWishesData(result)
    } catch (err) {
      setError(err as Error)
      console.error('Error collecting wishes:', err)
    } finally {
      setIsCollecting(false)
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Collection Controls */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">
          Colectare Wish-uri
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Surse
            </label>
            <div className="space-y-2">
              {['reddit', 'quora', 'gumtree', 'mumsnet', 'moneysavingexpert', 'indiehackers', 'hackernews', 'producthunt', 'youtube', 'softpedia', 'studentroom', 'ukbusinessforums', 'imobiliare', 'trustpilot', 'petitiideclic', 'undelucram', 'anpc'].map((source) => (
                <label key={source} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={sources.includes(source)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSources([...sources, source])
                      } else {
                        setSources(sources.filter((s) => s !== source))
                      }
                    }}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700 capitalize">
                    {source}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Limită
            </label>
            <input
              type="number"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value) || 50)}
              min={1}
              max={1000}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleCollect}
              disabled={isCollecting || sources.length === 0}
              className="w-full px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isCollecting ? 'Colectare...' : 'Colectează Wish-uri'}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Colectare wish-uri...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">
            Eroare: {(error as Error).message}
          </p>
        </div>
      )}

      {wishesData && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold text-gray-800">
              Wish-uri Colectate ({wishesData.total})
            </h2>
            <div className="text-sm text-gray-600">
              Filtre aplicate: {JSON.stringify(wishesData.filters_applied)}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {wishesData.wishes
              .sort((a: WishData, b: WishData) => b.business_score - a.business_score)
              .map((wish: WishData) => (
                <WishCard key={wish.id} wish={wish} />
              ))}
          </div>
        </div>
      )}

      {!wishesData && !isLoading && !error && (
        <div className="text-center py-12 bg-white rounded-lg shadow-md">
          <p className="text-gray-600">
            Apasă "Colectează Wish-uri" pentru a începe
          </p>
        </div>
      )}
    </div>
  )
}
