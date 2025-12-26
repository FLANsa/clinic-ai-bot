"use client"

import { useState, useEffect } from 'react'
import { getBranches } from '../../lib/api-client'

interface Branch {
  id: string
  name: string
  city: string
  address: string
  phone: string
  working_hours: string | object
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
      setLoading(true)
      setError(null)
      // إضافة timestamp لمنع cache
      const timestamp = new Date().getTime()
      const data = await getBranches()
      console.log('📊 البيانات المستلمة من API (fresh):', data)
      const branchesList = data.branches || []
      console.log(`✅ تم جلب ${branchesList.length} فرع من قاعدة البيانات في ${new Date().toLocaleTimeString()}`)
      
      if (branchesList.length === 0) {
        console.warn('⚠️ قاعدة البيانات فارغة - لا توجد فروع')
      }
      
      setBranches(branchesList)
    } catch (err: any) {
      setError(err.message || 'فشل في جلب الفروع من قاعدة البيانات')
      console.error('❌ خطأ في جلب الفروع:', err)
      setBranches([]) // تأكد من إفراغ القائمة في حالة الخطأ
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
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🏢 الفروع</h1>
          <p className="text-gray-600 mt-1">فروع العيادة ومواقعها - البيانات من قاعدة البيانات</p>
        </div>
        <button
          onClick={fetchBranches}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors duration-200"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              جاري التحديث...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              تحديث
            </>
          )}
        </button>
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

      {branches.length === 0 && !loading && (
        <div className="text-center py-12">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 max-w-md mx-auto">
            <div className="text-4xl mb-3">🏢</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">لا توجد فروع في قاعدة البيانات</h3>
            <p className="text-sm text-gray-600 mb-4">
              قاعدة البيانات فارغة من الفروع. استخدم زر "إضافة بيانات تجريبية" في صفحة Test Chat لإضافة فروع.
            </p>
            <button
              onClick={() => window.location.href = '/test-chat'}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold text-sm"
            >
              اذهب إلى Test Chat
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
