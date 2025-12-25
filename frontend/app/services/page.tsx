"use client"

import { useState, useEffect } from 'react'

interface Service {
  id: string
  name: string
  description: string
  base_price: number
  is_active: boolean
}

export default function ServicesPage() {
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchServices()
  }, [])

  const fetchServices = async () => {
    try {
      const res = await fetch('http://localhost:8000/admin/services', {
        headers: { 'X-API-Key': 'clinic-admin-secure-key-2024' }
      })
      if (!res.ok) throw new Error('فشل في جلب الخدمات')
      const data = await res.json()
      setServices(data.services || [])
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
        <h1 className="text-2xl font-bold text-gray-900">🏥 الخدمات</h1>
        <p className="text-gray-600 mt-1">إدارة خدمات العيادة</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {services.map((service) => (
          <div
            key={service.id}
            className={`bg-white rounded-xl shadow-sm border p-5 hover:shadow-md transition-shadow ${
              !service.is_active ? 'opacity-60' : ''
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-semibold text-gray-900">{service.name}</h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                service.is_active 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {service.is_active ? 'نشط' : 'غير نشط'}
              </span>
            </div>
            <p className="text-gray-600 text-sm mb-3 line-clamp-2">
              {service.description || 'لا يوجد وصف'}
            </p>
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
              <span className="text-lg font-bold text-blue-600">
                {service.base_price} ريال
              </span>
            </div>
          </div>
        ))}
      </div>

      {services.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          لا توجد خدمات حالياً
        </div>
      )}
    </div>
  )
}
