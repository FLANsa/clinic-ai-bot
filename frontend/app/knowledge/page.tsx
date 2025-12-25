"use client"

import { useState, useEffect } from 'react'

interface DocumentSource {
  id: string
  title: string
  source_type: string
  tags: string[]
  created_at: string
}

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<DocumentSource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const res = await fetch('http://localhost:8000/admin/rag/sources', {
        headers: { 'X-API-Key': 'clinic-admin-secure-key-2024' }
      })
      if (!res.ok) throw new Error('فشل في جلب الوثائق')
      const data = await res.json()
      setDocuments(data.sources || data.documents || [])
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const typeIcons: Record<string, string> = {
    policy: '📋',
    pdf: '📄',
    webpage: '🌐',
    text: '📝',
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
        <h1 className="text-2xl font-bold text-gray-900">📚 قاعدة المعرفة</h1>
        <p className="text-gray-600 mt-1">الوثائق والمصادر التي يستخدمها البوت</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="bg-white rounded-xl shadow-sm border p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-3 mb-3">
              <span className="text-2xl">{typeIcons[doc.source_type] || '📄'}</span>
              <div>
                <h3 className="font-semibold text-gray-900">{doc.title}</h3>
                <p className="text-sm text-gray-500">{doc.source_type}</p>
              </div>
            </div>
            
            {doc.tags && doc.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-3">
                {doc.tags.map((tag, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded-full text-xs"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {documents.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          لا توجد وثائق حالياً
        </div>
      )}
    </div>
  )
}
