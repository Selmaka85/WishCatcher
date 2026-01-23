'use client'

import { useState, useEffect } from 'react'
import { productGapsApi, ProductGap, FBAAnalysis } from '@/lib/api'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ProductGaps() {
  const [activeTab, setActiveTab] = useState<'manual' | 'auto'>('auto')
  
  // Manual search
  const [category, setCategory] = useState('')
  const [maxPrice, setMaxPrice] = useState<number | undefined>()
  const [isSearching, setIsSearching] = useState(false)
  const [gaps, setGaps] = useState<ProductGap[]>([])
  const [totalFound, setTotalFound] = useState(0)
  
  // Auto gaps
  const [autoGaps, setAutoGaps] = useState<any[]>([])
  const [isLoadingAuto, setIsLoadingAuto] = useState(false)
  const [autoStats, setAutoStats] = useState<any>(null)
  const [filterOpportunity, setFilterOpportunity] = useState<string>('')
  const [filterGapType, setFilterGapType] = useState<string>('')
  
  const [error, setError] = useState<Error | null>(null)

  const [selectedGap, setSelectedGap] = useState<ProductGap | null>(null)
  const [fbaAnalysis, setFbaAnalysis] = useState<FBAAnalysis | null>(null)
  const [isCalculating, setIsCalculating] = useState(false)

  // Load auto gaps on mount and when filters change
  useEffect(() => {
    if (activeTab === 'auto') {
      loadAutoGaps()
    }
  }, [activeTab, filterOpportunity, filterGapType])

  const loadAutoGaps = async () => {
    setIsLoadingAuto(true)
    setError(null)
    
    try {
      const params = new URLSearchParams()
      if (filterOpportunity) params.append('opportunity_type', filterOpportunity)
      if (filterGapType) params.append('gap_type', filterGapType)
      
      const response = await axios.get(`${API_URL}/api/product-gaps/auto?${params.toString()}`)
      setAutoGaps(response.data.gaps || [])
      setAutoStats(response.data.stats || null)
    } catch (err) {
      setError(err as Error)
      console.error('Error loading auto gaps:', err)
    } finally {
      setIsLoadingAuto(false)
    }
  }

  // FBA Calculator inputs
  const [amazonPrice, setAmazonPrice] = useState(0)
  const [importCosts, setImportCosts] = useState(0)
  const [fbaCosts, setFbaCosts] = useState(0)
  const [sellingPrice, setSellingPrice] = useState(0)
  const [quantity, setQuantity] = useState(1)

  const handleSearch = async () => {
    if (!category.trim()) {
      setError(new Error('Trebuie să introduci o categorie'))
      return
    }

    setIsSearching(true)
    setError(null)

    try {
      const result = await productGapsApi.search(category, maxPrice, false)
      setGaps(result.gaps || [])
      setTotalFound(result.total_found || 0)
    } catch (err) {
      setError(err as Error)
      console.error('Error searching product gaps:', err)
    } finally {
      setIsSearching(false)
    }
  }

  const handleCalculateFBA = async () => {
    if (!selectedGap) return

    setIsCalculating(true)
    setError(null)

    try {
      // Use selected gap prices or manual inputs
      const amazonPriceLei = selectedGap.amazon_uk_price ? selectedGap.amazon_uk_price * 5.5 : amazonPrice
      const sellingPriceLei = selectedGap.emag_price || sellingPrice

      const result = await productGapsApi.calculateFBA(
        amazonPriceLei,
        importCosts,
        fbaCosts,
        sellingPriceLei,
        quantity
      )
      setFbaAnalysis(result)
    } catch (err) {
      setError(err as Error)
      console.error('Error calculating FBA:', err)
    } finally {
      setIsCalculating(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const badges = {
      missing: { text: 'Lipsește', color: 'bg-red-100 text-red-800' },
      expensive: { text: 'Scump', color: 'bg-yellow-100 text-yellow-800' },
      available: { text: 'Disponibil', color: 'bg-green-100 text-green-800' }
    }
    const badge = badges[status as keyof typeof badges] || badges.missing
    return <span className={`px-2 py-1 rounded text-xs font-semibold ${badge.color}`}>{badge.text}</span>
  }

  const getRiskBadge = (risk: string) => {
    const badges = {
      low: { text: 'Risc Mic', color: 'bg-green-100 text-green-800' },
      medium: { text: 'Risc Mediu', color: 'bg-yellow-100 text-yellow-800' },
      high: { text: 'Risc Mare', color: 'bg-red-100 text-red-800' }
    }
    const badge = badges[risk as keyof typeof badges] || badges.medium
    return <span className={`px-2 py-1 rounded text-xs font-semibold ${badge.color}`}>{badge.text}</span>
  }

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="border-b border-gray-200 mb-4">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('auto')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'auto'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Gap-uri Automate ({autoStats?.total || 0})
            </button>
            <button
              onClick={() => setActiveTab('manual')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'manual'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Căutare Manuală
            </button>
          </nav>
        </div>
      </div>

      {/* Auto Gaps Tab */}
      {activeTab === 'auto' && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Gap-uri Identificate Automat
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tip Oportunitate
                </label>
                <select
                  value={filterOpportunity}
                  onChange={(e) => setFilterOpportunity(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                >
                  <option value="">Toate</option>
                  <option value="fba_import">FBA Import</option>
                  <option value="export">Export</option>
                  <option value="dropshipping">Dropshipping</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tip Gap
                </label>
                <select
                  value={filterGapType}
                  onChange={(e) => setFilterGapType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                >
                  <option value="">Toate</option>
                  <option value="missing">Lipsește</option>
                  <option value="expensive">Scump</option>
                  <option value="missing_multi">Lipsește Multi</option>
                </select>
              </div>
            </div>

            {autoStats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-gray-600">Total Gap-uri</div>
                  <div className="text-lg font-semibold text-gray-900">{autoStats.total}</div>
                </div>
                <div>
                  <div className="text-gray-600">FBA Import</div>
                  <div className="text-lg font-semibold text-blue-600">
                    {autoStats.by_opportunity?.fba_import || 0}
                  </div>
                </div>
                <div>
                  <div className="text-gray-600">Export</div>
                  <div className="text-lg font-semibold text-green-600">
                    {autoStats.by_opportunity?.export || 0}
                  </div>
                </div>
                <div>
                  <div className="text-gray-600">Dropshipping</div>
                  <div className="text-lg font-semibold text-purple-600">
                    {autoStats.by_opportunity?.dropshipping || 0}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Auto Gaps Table */}
          {isLoadingAuto ? (
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="text-gray-600">Se încarcă gap-urile...</div>
            </div>
          ) : autoGaps.length > 0 ? (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Rezultate ({autoGaps.length})
              </h2>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Produs</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">De la</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">La</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tip</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Oportunitate</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Profit Margin</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risc</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {autoGaps.map((gap, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">
                          {gap.product_name}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 capitalize">
                          {gap.from_marketplace}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 capitalize">
                          {gap.to_marketplace}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {getStatusBadge(gap.type)}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 capitalize">
                          {gap.opportunity_type?.replace('_', ' ')}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {gap.profit_margin ? (
                            <span className={gap.profit_margin > 30 ? 'text-green-600 font-semibold' : 'text-gray-600'}>
                              {gap.profit_margin.toFixed(1)}%
                            </span>
                          ) : 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {getRiskBadge(gap.risk_level)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="text-gray-600">
                Nu s-au găsit gap-uri automat identificate. Colectează wish-uri pentru a identifica gap-uri automat.
              </div>
            </div>
          )}
        </div>
      )}

      {/* Manual Search Tab */}
      {activeTab === 'manual' && (
        <>
          {/* Search Interface */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              Caută Produse Lipsă (eMAG vs Amazon)
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Categorie Produs
                </label>
                <input
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  placeholder="ex: laptop, căști, smartwatch"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Preț Maxim (lei)
                </label>
                <input
                  type="number"
                  value={maxPrice || ''}
                  onChange={(e) => setMaxPrice(e.target.value ? parseFloat(e.target.value) : undefined)}
                  placeholder="Opțional"
                  min={0}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                />
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleSearch}
                  disabled={isSearching || !category.trim()}
                  className="w-full px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isSearching ? 'Căutare...' : 'Caută Gap-uri'}
                </button>
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error.message}
              </div>
            )}

            {totalFound > 0 && (
              <div className="mt-4 text-sm text-gray-600">
                Găsite <strong>{totalFound}</strong> gap-uri de produse
              </div>
            )}
          </div>

          {/* Results Table */}
          {gaps.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                Rezultate ({gaps.length})
              </h2>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Produs</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status eMAG</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Preț Amazon UK</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Preț eMAG</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Marja Profit</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risc</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Acțiuni</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {gaps.map((gap, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">
                          <div className="flex items-center">
                            {gap.image_url && (
                              <img src={gap.image_url} alt={gap.product_name} className="w-10 h-10 rounded mr-2" />
                            )}
                            <span className="font-medium text-gray-900">{gap.product_name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm">{getStatusBadge(gap.emag_status)}</td>
                        <td className="px-4 py-3 text-sm">
                          {gap.amazon_uk_price ? `£${gap.amazon_uk_price.toFixed(2)}` : 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {gap.emag_price ? `${gap.emag_price.toFixed(2)} lei` : 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {gap.profit_margin ? (
                            <span className={gap.profit_margin > 30 ? 'text-green-600 font-semibold' : 'text-gray-600'}>
                              {gap.profit_margin.toFixed(1)}%
                            </span>
                          ) : 'N/A'}
                        </td>
                        <td className="px-4 py-3 text-sm">{getRiskBadge(gap.risk_level)}</td>
                        <td className="px-4 py-3 text-sm">
                          <button
                            onClick={() => {
                              setSelectedGap(gap)
                              if (gap.amazon_uk_price) setAmazonPrice(gap.amazon_uk_price * 5.5)
                              if (gap.emag_price) setSellingPrice(gap.emag_price)
                            }}
                            className="text-primary-600 hover:text-primary-700 font-medium"
                          >
                            Analizează FBA
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* FBA Calculator */}
          {selectedGap && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                FBA Calculator - {selectedGap.product_name}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preț Amazon (lei)
                  </label>
                  <input
                    type="number"
                    value={amazonPrice}
                    onChange={(e) => setAmazonPrice(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Costuri Import (lei)
                  </label>
                  <input
                    type="number"
                    value={importCosts}
                    onChange={(e) => setImportCosts(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Costuri FBA (lei)
                  </label>
                  <input
                    type="number"
                    value={fbaCosts}
                    onChange={(e) => setFbaCosts(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Preț Vânzare (lei)
                  </label>
                  <input
                    type="number"
                    value={sellingPrice}
                    onChange={(e) => setSellingPrice(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Cantitate
                  </label>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                    min={1}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                  />
                </div>
              </div>

              <button
                onClick={handleCalculateFBA}
                disabled={isCalculating || !amazonPrice || !sellingPrice}
                className="w-full md:w-auto px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isCalculating ? 'Calculare...' : 'Calculează Profitabilitate'}
              </button>

              {fbaAnalysis && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3">Rezultate Analiză FBA</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">Profit Brut</div>
                      <div className="text-lg font-semibold text-gray-900">{fbaAnalysis.profit_brut.toFixed(2)} lei</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Profit Net</div>
                      <div className="text-lg font-semibold text-green-600">{fbaAnalysis.profit_net.toFixed(2)} lei</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">ROI</div>
                      <div className="text-lg font-semibold text-blue-600">{fbaAnalysis.roi.toFixed(1)}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Break-Even</div>
                      <div className="text-lg font-semibold text-gray-900">{fbaAnalysis.break_even_units} unități</div>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="text-sm text-gray-600 mb-1">Risc: {getRiskBadge(fbaAnalysis.risk_level)}</div>
                    <div className="text-sm text-gray-700">{fbaAnalysis.recommendation}</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
