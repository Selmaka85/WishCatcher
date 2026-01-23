'use client'

import { useState } from 'react'

interface FiltersProps {
  filters: any
  setFilters: (filters: any) => void
}

export default function Filters({ filters, setFilters }: FiltersProps) {
  const [isOpen, setIsOpen] = useState(false)

  const updateFilter = (key: string, value: any) => {
    setFilters({
      ...filters,
      [key]: value,
    })
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Filtre</h2>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-primary-600 hover:text-primary-700"
        >
          {isOpen ? 'Ascunde' : 'Afișează'}
        </button>
      </div>

      {isOpen && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Geography Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Geografie
            </label>
            <select
              value={filters.geography?.level || 'global'}
              onChange={(e) =>
                updateFilter('geography', {
                  ...filters.geography,
                  level: e.target.value,
                })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
            >
              <option value="global">Global</option>
              <option value="uk">UK / Anglia</option>
              <option value="romania">România</option>
            </select>

            {filters.geography?.level === 'uk' && (
              <select
                className="w-full mt-2 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                onChange={(e) =>
                  updateFilter('geography', {
                    ...filters.geography,
                    country: e.target.value,
                  })
                }
              >
                <option value="united_kingdom">United Kingdom</option>
                <option value="london">London</option>
                <option value="manchester">Manchester</option>
              </select>
            )}

            {filters.geography?.level === 'romania' && (
              <select
                className="w-full mt-2 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
                onChange={(e) =>
                  updateFilter('geography', {
                    ...filters.geography,
                    country: e.target.value,
                  })
                }
              >
                <option value="romania">România</option>
                <option value="bucuresti">București</option>
                <option value="cluj">Cluj-Napoca</option>
              </select>
            )}
          </div>

          {/* Language Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Limbă
            </label>
            <select
              value={filters.language || 'all'}
              onChange={(e) => updateFilter('language', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
            >
              <option value="all">Toate limbile</option>
              <option value="en">Engleză</option>
              <option value="ro">Română</option>
            </select>
          </div>

          {/* Domain Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Domeniu
            </label>
            <select
              value={filters.domain || 'all'}
              onChange={(e) => updateFilter('domain', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 text-gray-900 bg-white"
            >
              <option value="all">Toate domeniile</option>
              <option value="software">Software</option>
              <option value="finance">Finance</option>
              <option value="health">Health</option>
              <option value="education">Education</option>
            </select>
          </div>
        </div>
      )}
    </div>
  )
}
