"use client"

import { useState, useEffect } from 'react'

interface FAQ {
  id: string
  question: string
  answer: string
}

export default function FAQPage() {
  const [faqs, setFaqs] = useState<FAQ[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [openId, setOpenId] = useState<string | null>(null)

  useEffect(() => {
    fetchFAQs()
  }, [])

  const fetchFAQs = async () => {
    try {
      const res = await fetch('http://localhost:8000/admin/faqs', {
        headers: { 'X-API-Key': 'clinic-admin-secure-key-2024' }
      })
      if (!res.ok) throw new Error('فشل في جلب الأسئلة')
      const data = await res.json()
      setFaqs(data.faqs || [])
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
        <h1 className="text-2xl font-bold text-gray-900">❓ الأسئلة الشائعة</h1>
        <p className="text-gray-600 mt-1">الأسئلة المتكررة وإجاباتها</p>
      </div>

      <div className="space-y-3 max-w-3xl">
        {faqs.map((faq) => (
          <div
            key={faq.id}
            className="bg-white rounded-xl shadow-sm border overflow-hidden"
          >
            <button
              onClick={() => setOpenId(openId === faq.id ? null : faq.id)}
              className="w-full px-5 py-4 text-right flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <span className="font-medium text-gray-900">{faq.question}</span>
              <svg
                className={`w-5 h-5 text-gray-500 transition-transform ${
                  openId === faq.id ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {openId === faq.id && (
              <div className="px-5 py-4 bg-gray-50 border-t border-gray-100">
                <p className="text-gray-600 leading-relaxed">{faq.answer}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {faqs.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          لا توجد أسئلة حالياً
        </div>
      )}
    </div>
  )
}
