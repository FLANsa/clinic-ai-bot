"use client"

import { useState, useEffect } from 'react'
import { getAppointments } from '../../lib/api-client'

interface Appointment {
  id: string
  patient_name: string
  phone: string
  datetime: string
  status: string
  channel: string
  notes: string
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchAppointments()
  }, [])

  const fetchAppointments = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getAppointments()
      setAppointments(data.appointments || [])
    } catch (err: any) {
      setError(err.message || 'فشل في جلب المواعيد')
      console.error('❌ خطأ في جلب المواعيد:', err)
      setAppointments([])
    } finally {
      setLoading(false)
    }
  }

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'confirmed': return 'bg-green-100 text-green-700'
      case 'pending': return 'bg-yellow-100 text-yellow-700'
      case 'cancelled': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'confirmed': return 'مؤكد'
      case 'pending': return 'قيد الانتظار'
      case 'cancelled': return 'ملغي'
      default: return status
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('ar-SA', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
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
          {error}
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">📅 المواعيد</h1>
        <p className="text-gray-600 mt-1">إدارة مواعيد العملاء</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">المريض</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">الهاتف</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">التاريخ</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">القناة</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-700">الحالة</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {appointments.map((apt) => (
                <tr key={apt.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4">
                    <div className="font-medium text-gray-900">{apt.patient_name}</div>
                    {apt.notes && (
                      <div className="text-sm text-gray-500 mt-1">{apt.notes}</div>
                    )}
                  </td>
                  <td className="px-4 py-4 text-gray-600" dir="ltr">{apt.phone}</td>
                  <td className="px-4 py-4 text-gray-600 text-sm">{formatDate(apt.datetime)}</td>
                  <td className="px-4 py-4 text-gray-600">{apt.channel}</td>
                  <td className="px-4 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusStyle(apt.status)}`}>
                      {getStatusLabel(apt.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {appointments.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          لا توجد مواعيد حالياً
        </div>
      )}
    </div>
  )
}
