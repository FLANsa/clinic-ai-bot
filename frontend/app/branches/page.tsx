"use client"

import { useState, useEffect } from 'react'

interface Branch {
  id: string
  name: string
  city: string
  address: string
  phone: string
  working_hours: string
  is_active: boolean
}

export default function BranchesPage() {
  const [branches, setBranches] = useState<Branch[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchBranches()
  }, [])

  const fetchBranches = async () => {
    try {
      const res = await fetch('http://localhost:8000/admin/branches', {
        headers: { 'X-API-Key': 'clinic-admin-secure-key-2024' }
      })
      if (!res.ok) throw new Error('فشل في جلب الفروع')
      const data = await res.json()
      setBranches(data.branches || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          ❌ {error}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">🏢 الفروع</h1>
        <p className="text-gray-600 mt-1">فروع العيادة ومواقعها</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {branches.map((branch) => (
          <div
            key={branch.id}
            className={`bg-white rounded-xl shadow-sm border p-5 hover:shadow-md transition-shadow ${
              !branch.is_active ? 'opacity-60' : ''
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-gray-900 text-lg">{branch.name}</h3>
                <p className="text-blue-600 text-sm">{branch.city}</p>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                branch.is_active 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {branch.is_active ? 'مفتوح' : 'مغلق'}
              </span>
            </div>
            
            <div className="space-y-2 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <span>📍</span>
                <span>{branch.address || 'لا يوجد عنوان'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span>📞</span>
                <span dir="ltr">{branch.phone || 'لا يوجد رقم'}</span>
              </div>
              {branch.working_hours && typeof branch.working_hours === 'string' && (
                <div className="flex items-center gap-2">
                  <span>🕐</span>
                  <span>{branch.working_hours}</span>
                </div>
              )}
              {branch.working_hours && typeof branch.working_hours === 'object' && (
                <div className="flex items-center gap-2">
                  <span>🕐</span>
                  <span>متاح حسب الطلب</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {branches.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          لا توجد فروع حالياً
        </div>
      )}
    </div>
  )
}
