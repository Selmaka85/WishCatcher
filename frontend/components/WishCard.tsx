'use client'

import { useState } from 'react'
import { WishData } from '@/lib/api'
import { businessPlansApi, mvpApi } from '@/lib/api'
import { format } from 'date-fns'
import { ChevronDown, ChevronUp, TrendingUp, DollarSign, Clock } from 'lucide-react'

interface WishCardProps {
  wish: WishData
}

export default function WishCard({ wish }: WishCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [businessPlan, setBusinessPlan] = useState<any>(null)
  const [mvp, setMvp] = useState<any>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerateBusinessPlan = async () => {
    setIsGenerating(true)
    try {
      const bp = await businessPlansApi.generate(wish.id, true)
      setBusinessPlan(bp)
    } catch (error) {
      console.error('Error generating business plan:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleGenerateMVP = async () => {
    setIsGenerating(true)
    try {
      const mvpData = await mvpApi.generate(
        wish.id,
        businessPlan?.id
      )
      setMvp(mvpData)
    } catch (error) {
      console.error('Error generating MVP:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {wish.intent}
          </h3>
          <div className="flex flex-wrap gap-2 mb-2">
            <span className="px-2 py-1 bg-primary-100 text-primary-800 rounded text-xs font-medium">
              {wish.domain}
            </span>
            <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">
              {wish.source}
            </span>
            {wish.technologies.map((tech) => (
              <span
                key={tech}
                className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div
            className={`px-3 py-1 rounded-full text-sm font-semibold ${getScoreColor(
              wish.business_score
            )}`}
          >
            {Math.round(wish.business_score * 100)}%
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-500 hover:text-gray-700"
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600">
            Score: {Math.round(wish.score * 100)}%
          </span>
        </div>
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600">
            Feasibility: {wish.feasibility}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600">
            {format(new Date(wish.timestamp), 'dd MMM yyyy')}
          </span>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
          {/* Trigger Analysis */}
          {wish.trigger_analysis && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">
                Trigger Analysis
              </h4>
              {wish.trigger_analysis.trigger?.text && (
                <div className="mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    Trigger:
                  </span>
                  <p className="text-sm text-gray-600">
                    {wish.trigger_analysis.trigger.text}
                  </p>
                </div>
              )}
              {wish.trigger_analysis.pain_points &&
                wish.trigger_analysis.pain_points.length > 0 && (
                  <div className="mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      Pain Points:
                    </span>
                    <ul className="list-disc list-inside text-sm text-gray-600">
                      {wish.trigger_analysis.pain_points.map((pp, idx) => (
                        <li key={idx}>
                          {pp.text} ({pp.severity})
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              {wish.trigger_analysis.emotional_intensity && (
                <div>
                  <span className="text-sm font-medium text-gray-700">
                    Emotional Intensity:
                  </span>
                  <span className="text-sm text-gray-600 ml-2">
                    {Math.round(
                      wish.trigger_analysis.emotional_intensity * 100
                    )}
                    %
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Market Analysis */}
          {wish.market_analysis && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">
                Market Analysis
              </h4>
              <div className="text-sm text-gray-600">
                <p>
                  Market Size: {wish.market_analysis.market_size || 'N/A'}
                </p>
                <p>
                  Target: {wish.market_analysis.target_demographic || 'N/A'}
                </p>
              </div>
            </div>
          )}

          {/* Monetization */}
          {wish.monetization && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">
                Monetization
              </h4>
              <div className="text-sm text-gray-600">
                <p>Model: {wish.monetization.model || 'N/A'}</p>
                <p>Price: {wish.monetization.estimated_price || 'N/A'}</p>
                <p>
                  Revenue: {wish.monetization.potential_revenue || 'N/A'}
                </p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-4 border-t border-gray-200">
            <button
              onClick={handleGenerateBusinessPlan}
              disabled={isGenerating}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm"
            >
              {isGenerating
                ? 'Generare...'
                : businessPlan
                ? 'Business Plan Generat'
                : 'Generează Business Plan'}
            </button>

            {businessPlan && (
              <button
                onClick={handleGenerateMVP}
                disabled={isGenerating}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm"
              >
                {isGenerating
                  ? 'Generare...'
                  : mvp
                  ? 'MVP Generat'
                  : 'Generează MVP'}
              </button>
            )}
          </div>

          {/* Business Plan Preview */}
          {businessPlan && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold text-gray-800 mb-2">
                Business Plan Preview
              </h4>
              <div className="text-sm text-gray-600 space-y-1">
                <p>
                  <strong>Value Proposition:</strong>{' '}
                  {businessPlan.executive_summary?.value_proposition || 'N/A'}
                </p>
                <p>
                  <strong>Market:</strong>{' '}
                  {businessPlan.market_analysis?.target_market?.size || 'N/A'}
                </p>
                <p>
                  <strong>Revenue Model:</strong>{' '}
                  {businessPlan.business_model?.revenue_streams?.[0]?.type ||
                    'N/A'}
                </p>
              </div>
            </div>
          )}

          {/* MVP Preview */}
          {mvp && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-semibold text-gray-800 mb-2">
                MVP Structure
              </h4>
              <div className="text-sm text-gray-600">
                <p>
                  <strong>Files:</strong> {mvp.files?.length || 0} fișiere
                  generate
                </p>
                <div className="mt-2">
                  <button
                    onClick={() => {
                      // Download MVP as ZIP (simplified)
                      const dataStr = JSON.stringify(mvp, null, 2)
                      const dataBlob = new Blob([dataStr], {
                        type: 'application/json',
                      })
                      const url = URL.createObjectURL(dataBlob)
                      const link = document.createElement('a')
                      link.href = url
                      link.download = `mvp_${wish.id}.json`
                      link.click()
                    }}
                    className="text-primary-600 hover:text-primary-700 text-sm underline"
                  >
                    Download MVP Structure
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
