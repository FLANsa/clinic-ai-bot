"use client"

import { useState, useEffect } from 'react'
import { getServices, createService, updateService, deleteService } from '../../lib/api-client'

interface Service {
  id: string
  name: string
  description: string
  base_price: number | null
  is_active: boolean
}

interface ServiceModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: Partial<Service>) => Promise<void>
  service?: Service | null
}

function ServiceModal({ isOpen, onClose, onSave, service }: ServiceModalProps) {
  const [formData, setFormData] = useState<Partial<Service>>({
    name: '',
    description: '',
    base_price: null,
    is_active: true
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (service) {
      setFormData(service)
    } else {
      setFormData({
        name: '',
        description: '',
        base_price: null,
        is_active: true
      })
    }
  }, [service, isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await onSave(formData)
      onClose()
    } catch (error) {
      alert(`خطأ: ${error instanceof Error ? error.message : 'حدث خطأ غير متوقع'}`)
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">{service ? 'تعديل خدمة' : 'إضافة خدمة جديدة'}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">اسم الخدمة *</label>
            <input
              type="text"
              required
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">الوصف</label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">السعر (ريال سعودي)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.base_price || ''}
              onChange={(e) => setFormData({ ...formData, base_price: e.target.value ? parseFloat(e.target.value) : null })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              checked={formData.is_active ?? true}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label className="mr-2 text-sm font-medium text-gray-700">نشط</label>
          </div>

          <div className="flex gap-3 justify-end pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              إلغاء
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400"
            >
              {saving ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function ServicesPage() {
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingService, setEditingService] = useState<Service | null>(null)
  const [deletingService, setDeletingService] = useState<string | null>(null)

  useEffect(() => {
    fetchServices()
  }, [])

  const fetchServices = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getServices()
      setServices(data.services || [])
    } catch (err: any) {
      setError(err.message || 'فشل في جلب الخدمات')
      console.error('❌ خطأ في جلب الخدمات:', err)
      setServices([])
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingService(null)
    setModalOpen(true)
  }

  const handleEdit = (service: Service) => {
    setEditingService(service)
    setModalOpen(true)
  }

  const handleSave = async (data: Partial<Service>) => {
    try {
      if (editingService) {
        await updateService(editingService.id, data)
      } else {
        await createService(data)
      }
      await fetchServices()
      setModalOpen(false)
      setEditingService(null)
    } catch (error) {
      throw error
    }
  }

  const handleDelete = async (serviceId: string) => {
    if (!confirm('هل أنت متأكد من حذف هذه الخدمة؟')) {
      return
    }

    try {
      setDeletingService(serviceId)
      await deleteService(serviceId)
      await fetchServices()
      alert('تم حذف الخدمة بنجاح')
    } catch (error: any) {
      alert(`خطأ: ${error.message || 'حدث خطأ غير متوقع'}`)
    } finally {
      setDeletingService(null)
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
          <h1 className="text-2xl font-bold text-gray-900">🏥 الخدمات</h1>
          <p className="text-gray-600 mt-1">إدارة خدمات العيادة</p>
        </div>
        <button
          onClick={handleAdd}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          إضافة خدمة جديدة
        </button>
      </div>

      {services.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">لا توجد خدمات حالياً</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الاسم</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الوصف</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">السعر</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الحالة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {services.map((service) => (
                <tr key={service.id} className={!service.is_active ? 'opacity-60' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{service.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">{service.description || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {service.base_price !== null ? `${service.base_price} ريال` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      service.is_active 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {service.is_active ? 'نشط' : 'غير نشط'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(service)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        تعديل
                      </button>
                      <button
                        onClick={() => handleDelete(service.id)}
                        disabled={deletingService === service.id}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                      >
                        {deletingService === service.id ? 'جاري الحذف...' : 'حذف'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ServiceModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setEditingService(null)
        }}
        onSave={handleSave}
        service={editingService}
      />
    </div>
  )
}
