"use client"

import { useState, useEffect } from 'react'
import { getDoctors, createDoctor, updateDoctor, deleteDoctor, getBranches } from '../../lib/api-client'

interface Doctor {
  id: string
  name: string
  specialty: string
  branch_id?: string
  license_number?: string
  phone_number?: string
  email?: string
  bio?: string
  working_hours?: any
  qualifications?: string
  experience_years?: string
  is_active: boolean
}

interface Branch {
  id: string
  name: string
}

interface DoctorModalProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: Partial<Doctor>) => Promise<void>
  doctor?: Doctor | null
  branches: Branch[]
}

function DoctorModal({ isOpen, onClose, onSave, doctor, branches }: DoctorModalProps) {
  const [formData, setFormData] = useState<Partial<Doctor>>({
    name: '',
    specialty: '',
    branch_id: '',
    license_number: '',
    phone_number: '',
    email: '',
    bio: '',
    working_hours: {},
    qualifications: '',
    experience_years: '',
    is_active: true
  })
  const [saving, setSaving] = useState(false)
  const [workingHoursJson, setWorkingHoursJson] = useState('')

  useEffect(() => {
    if (doctor) {
      setFormData(doctor)
      setWorkingHoursJson(JSON.stringify(doctor.working_hours || {}, null, 2))
    } else {
      setFormData({
        name: '',
        specialty: '',
        branch_id: branches[0]?.id || '',
        license_number: '',
        phone_number: '',
        email: '',
        bio: '',
        working_hours: {},
        qualifications: '',
        experience_years: '',
        is_active: true
      })
      setWorkingHoursJson('{}')
    }
  }, [doctor, isOpen, branches])

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
          <h2 className="text-2xl font-bold">{doctor ? 'تعديل طبيب' : 'إضافة طبيب جديد'}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">اسم الطبيب *</label>
            <input
              type="text"
              required
              value={formData.name || ''}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">التخصص *</label>
            <input
              type="text"
              required
              value={formData.specialty || ''}
              onChange={(e) => setFormData({ ...formData, specialty: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">الفرع *</label>
            <select
              required
              value={formData.branch_id || ''}
              onChange={(e) => setFormData({ ...formData, branch_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">اختر الفرع</option>
              {branches.map((branch) => (
                <option key={branch.id} value={branch.id}>{branch.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">رقم الترخيص</label>
            <input
              type="text"
              value={formData.license_number || ''}
              onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">رقم الهاتف</label>
            <input
              type="text"
              value={formData.phone_number || ''}
              onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">البريد الإلكتروني</label>
            <input
              type="email"
              value={formData.email || ''}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">النبذة</label>
            <textarea
              value={formData.bio || ''}
              onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">المؤهلات</label>
            <textarea
              value={formData.qualifications || ''}
              onChange={(e) => setFormData({ ...formData, qualifications: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">سنوات الخبرة</label>
            <input
              type="text"
              value={formData.experience_years || ''}
              onChange={(e) => setFormData({ ...formData, experience_years: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ساعات العمل (JSON)</label>
            <textarea
              value={workingHoursJson}
              onChange={(e) => setWorkingHoursJson(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              rows={6}
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

export default function DoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [branches, setBranches] = useState<Branch[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingDoctor, setEditingDoctor] = useState<Doctor | null>(null)
  const [deletingDoctor, setDeletingDoctor] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [doctorsData, branchesData] = await Promise.all([
        getDoctors(),
        getBranches()
      ])
      setDoctors(doctorsData.doctors || [])
      setBranches(branchesData.branches || [])
    } catch (err: any) {
      setError(err.message || 'فشل في جلب البيانات')
      console.error('❌ خطأ في جلب البيانات:', err)
      setDoctors([])
      setBranches([])
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingDoctor(null)
    setModalOpen(true)
  }

  const handleEdit = (doctor: Doctor) => {
    setEditingDoctor(doctor)
    setModalOpen(true)
  }

  const handleSave = async (data: Partial<Doctor>) => {
    try {
      if (editingDoctor) {
        await updateDoctor(editingDoctor.id, data)
      } else {
        await createDoctor(data)
      }
      await fetchData()
      setModalOpen(false)
      setEditingDoctor(null)
    } catch (error) {
      throw error
    }
  }

  const handleDelete = async (doctorId: string) => {
    if (!confirm('هل أنت متأكد من حذف هذا الطبيب؟')) {
      return
    }

    try {
      setDeletingDoctor(doctorId)
      await deleteDoctor(doctorId)
      await fetchData()
      alert('تم حذف الطبيب بنجاح')
    } catch (error: any) {
      alert(`خطأ: ${error.message || 'حدث خطأ غير متوقع'}`)
    } finally {
      setDeletingDoctor(null)
    }
  }

  const getBranchName = (branchId?: string) => {
    if (!branchId) return '-'
    const branch = branches.find(b => b.id === branchId)
    return branch?.name || '-'
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
          <h1 className="text-2xl font-bold text-gray-900">👨‍⚕️ الأطباء</h1>
          <p className="text-gray-600 mt-1">إدارة الأطباء في العيادة</p>
        </div>
        <button
          onClick={handleAdd}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          إضافة طبيب جديد
        </button>
      </div>

      {doctors.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">لا يوجد أطباء حالياً</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الاسم</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">التخصص</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الفرع</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">سنوات الخبرة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الحالة</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {doctors.map((doctor) => (
                <tr key={doctor.id} className={!doctor.is_active ? 'opacity-60' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{doctor.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{doctor.specialty}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{getBranchName(doctor.branch_id)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{doctor.experience_years || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      doctor.is_active 
                        ? 'bg-green-100 text-green-700' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {doctor.is_active ? 'نشط' : 'غير نشط'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(doctor)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        تعديل
                      </button>
                      <button
                        onClick={() => handleDelete(doctor.id)}
                        disabled={deletingDoctor === doctor.id}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                      >
                        {deletingDoctor === doctor.id ? 'جاري الحذف...' : 'حذف'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <DoctorModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setEditingDoctor(null)
        }}
        onSave={handleSave}
        doctor={editingDoctor}
        branches={branches}
      />
    </div>
  )
}
