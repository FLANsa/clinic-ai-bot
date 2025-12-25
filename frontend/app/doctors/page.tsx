"use client"

import { useState, useEffect } from 'react'

interface Doctor {
  id: string
  name: string
  specialty: string
  bio: string
  is_active: boolean
}

export default function DoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDoctors()
  }, [])

  const fetchDoctors = async () => {
    try {
      const res = await fetch('http://localhost:8000/admin/doctors', {
        headers: { 'X-API-Key': 'clinic-admin-secure-key-2024' }
      })
      if (!res.ok) throw new Error('فشل في جلب الأطباء')
      const data = await res.json()
      setDoctors(data.doctors || [])
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
        <h1 className="text-2xl font-bold text-gray-900">👨‍⚕️ الأطباء</h1>
        <p className="text-gray-600 mt-1">فريق الأطباء في العيادة</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {doctors.map((doctor) => (
          <div
            key={doctor.id}
            className={`bg-white rounded-xl shadow-sm border p-5 hover:shadow-md transition-shadow ${
              !doctor.is_active ? 'opacity-60' : ''
            }`}
          >
            <div className="flex items-center gap-4 mb-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white text-xl">
                👨‍⚕️
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{doctor.name}</h3>
                <p className="text-blue-600 text-sm">{doctor.specialty || 'طبيب عام'}</p>
              </div>
            </div>
            <p className="text-gray-600 text-sm line-clamp-3">
              {doctor.bio || 'لا توجد نبذة'}
            </p>
            <div className="mt-3 pt-3 border-t border-gray-100">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                doctor.is_active 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {doctor.is_active ? 'متاح' : 'غير متاح'}
              </span>
            </div>
          </div>
        ))}
      </div>

      {doctors.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          لا يوجد أطباء حالياً
        </div>
      )}
    </div>
  )
}
