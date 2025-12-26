"use client"

import { useState, useEffect } from 'react'
import { getOffers } from '../../lib/api-client'

interface Offer {
  id: string
  title: string
  description: string
  discount_type: string
  discount_value: number
  is_active: boolean
}

export default function OffersPage() {
  const [offers, setOffers] = useState<Offer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchOffers()
  }, [])

  const fetchOffers = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getOffers()
      setOffers(data.offers || [])
    } catch (err: any) {
      setError(err.message || 'فشل في جلب العروض')
      console.error('❌ خطأ في جلب العروض:', err)
      setOffers([])
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

  const formatDiscount = (offer: Offer) => {
    if (offer.discount_type === 'percentage') {
      return `${offer.discount_value}%`
    } else if (offer.discount_type === 'fixed') {
      return `${offer.discount_value} ريال`
    }
    return '-'
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">🎁 العروض</h1>
        <p className="text-gray-600 mt-1">عروض وخصومات العيادة</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {offers.map((offer) => (
          <div
            key={offer.id}
            className={`bg-white rounded-xl shadow-sm border p-5 hover:shadow-md transition-shadow ${
              !offer.is_active ? 'opacity-60' : ''
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-semibold text-gray-900">{offer.title}</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                offer.is_active 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {offer.is_active ? 'نشط' : 'غير نشط'}
              </span>
            </div>
            <p className="text-gray-600 text-sm mb-3 line-clamp-2">
              {offer.description || 'لا يوجد وصف'}
            </p>
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <span className="text-lg font-bold text-red-600">
                خصم {formatDiscount(offer)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {offers.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          لا توجد عروض حالياً
        </div>
      )}
    </div>
  )
}
