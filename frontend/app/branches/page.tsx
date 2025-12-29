"use client"

import { useState, useEffect } from 'react'
import { getBranches, createBranch, updateBranch, deleteBranch } from '../../lib/api-client'

interface Branch {
  id: string
  name: string
  city: string
  address: string
  phone: string
  location_url?: string
  working_hours: any
  is_active: boolean
}

interface BranchModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: Partial<Branch>) => Promise<void>
  branch?: Branch | null
}

function BranchModal({ isOpen, onClose, onSave, branch }: BranchModalProps) {
  const [formData, setFormData] = useState<Partial<Branch>>({
    name: '',
    city: '',
    address: '',
    phone: '',
    location_url: '',
    working_hours: {
      sunday: { from: '08:00', to: '20:00' },
      monday: { from: '08:00', to: '20:00' },
      tuesday: { from: '08:00', to: '20:00' },
      wednesday: { from: '08:00', to: '20:00' },
      thursday: { from: '08:00', to: '20:00' },
      friday: { from: '13:00', to: '20:00' },
      saturday: { from: '08:00', to: '20:00' }
    },
    is_active: true
  })
  const [saving, setSaving] = useState(false)
  const [workingHoursJson, setWorkingHoursJson] = useState('')

  useEffect(() => {
    if (branch) {
      setFormData(branch)
      setWorkingHoursJson(JSON.stringify(branch.working_hours || {}, null, 2))
    } else {
      setFormData({
        name: '',
        city: '',
        address: '',
        phone: '',
        location_url: '',
        working_hours: {
          sunday: { from: '08:00', to: '20:00' },
          monday: { from: '08:00', to: '20:00' },
          tuesday: { from: '08:00', to: '20:00' },
          wednesday: { from: '08:00', to: '20:00' },
          thursday: { from: '08:00', to: '20:00' },
          friday: { from: '13:00', to: '20:00' },
          saturday: { from: '08:00', to: '20:00' }
        },
        is_active: true
      })
      setWorkingHoursJson(JSON.stringify({
        sunday: { from: '08:00', to: '20:00' },
        monday: { from: '08:00', to: '20:00' },
        tuesday: { from: '08:00', to: '20:00' },
        wednesday: { from: '08:00', to: '20:00' },
        thursday: { from: '08:00', to: '20:00' },
        friday: { from: '13:00', to: '20:00' },
        saturday: { from: '08:00', to: '20:00' }
      }, null, 2))
    }
  }, [branch, isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      let workingHours = formData.working_hours
      if (workingHoursJson) {
        try {
          workingHours = JSON.parse(workingHoursJson)
        } catch {
          alert('خطأ في صيغة JSON لساعات العمل')
          setSaving(false)
          return
        }
      }
      await onSave({ ...formData, working_hours: workingHours })
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
          <h2 className="text-2xl font-bold">{branch ? 'تعديل فرع' : 'إضافة فرع جديد'}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">اسم الفرع *</label>
            <input
              type="text"
              required
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">المدينة *</label>
            <input
              type="text"
              required
              value={formData.city || ''}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">العنوان *</label>
            <textarea
              required
              value={formData.address || ''}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">رقم الهاتف</label>
            <input
              type="text"
              value={formData.phone || ''}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">رابط الخريطة</label>
            <input
              type="url"
              value={formData.location_url || ''}
              onChange={(e) => setFormData({ ...formData, location_url: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ساعات العمل (JSON)</label>
            <textarea
              value={workingHoursJson}
              onChange={(e) => setWorkingHoursJson(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              rows={8}
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

export default function BranchesPage() {
  const [branches, setBranches] = useState<Branch[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingBranch, setEditingBranch] = useState<Branch | null>(null)
  const [deletingBranch, setDeletingBranch] = useState<string | null>(null)

  useEffect(() => {
    fetchBranches()
  }, [])

  const fetchBranches = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getBranches()
      setBranches(data.branches || [])
    } catch (err: any) {
      setError(err.message || 'فشل في جلب الفروع')
      console.error('❌ خطأ في جلب الفروع:', err)
      setBranches([])
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingBranch(null)
    setModalOpen(true)
  }

  const handleEdit = (branch: Branch) => {
    setEditingBranch(branch)
    setModalOpen(true)
  }

  const handleSave = async (data: Partial<Branch>) => {
    try {
      if (editingBranch) {
        await updateBranch(editingBranch.id, data)
      } else {
        await createBranch(data)
      }
      await fetchBranches()
      setModalOpen(false)
      setEditingBranch(null)
    } catch (error) {
      throw error
    }
  }

  const handleDelete = async (branchId: string) => {
    if (!confirm('هل أنت متأكد من حذف هذا الفرع؟')) {
      return
    }

    try {
      setDeletingBranch(branchId)
      await deleteBranch(branchId)
      await fetchBranches()
      alert('تم حذف الفرع بنجاح')
    } catch (error: any) {
      alert(`خطأ: ${error.message || 'حدث خطأ غير متوقع'}`)
    } finally {
      setDeletingBranch(null)
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
          <p className="text-gray-600 mt-1">إدارة فروع العيادة</p>
        </div>
        <button
          onClick={handleAdd}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          إضافة فرع جديد
        </button>
      </div>

      {branches.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">لا توجد فروع حالياً</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الاسم</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">المدينة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">العنوان</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الهاتف</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الحالة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {branches.map((branch) => (
                <tr key={branch.id} className={!branch.is_active ? 'opacity-60' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{branch.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{branch.city}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{branch.address || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500" dir="ltr">{branch.phone || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      branch.is_active 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {branch.is_active ? 'نشط' : 'غير نشط'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(branch)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        تعديل
                      </button>
                      <button
                        onClick={() => handleDelete(branch.id)}
                        disabled={deletingBranch === branch.id}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                      >
                        {deletingBranch === branch.id ? 'جاري الحذف...' : 'حذف'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <BranchModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setEditingBranch(null)
        }}
        onSave={handleSave}
        branch={editingBranch}
      />
    </div>
  )
}
