"use client"

import { useState, useEffect } from 'react'

interface DailyStats {
  total_conversations: number
  total_appointments: number
  channels: Record<string, number>
  top_intents: Record<string, number>
}

export default function DailyReportsPage() {
  const [stats, setStats] = useState<DailyStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const res = await fetch('http://localhost:8000/admin/analytics/summary', {
        headers: { 'X-API-Key': 'clinic-admin-secure-key-2024' }
      })
      if (!res.ok) throw new Error('فشل في جلب الإحصائيات')
      const data = await res.json()
      setStats(data)
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

  const channelEmoji: Record<string, string> = {
    whatsapp: '💬',
    instagram: '📸',
    tiktok: '🎵',
    google_maps: '📍',
    web: '🌐',
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">📊 التقارير اليومية</h1>
        <p className="text-gray-600 mt-1">إحصائيات اليوم</p>
      </div>

      {stats && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <div className="text-3xl mb-2">💬</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_conversations}</div>
              <div className="text-gray-500 text-sm">محادثة</div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <div className="text-3xl mb-2">📅</div>
              <div className="text-2xl font-bold text-gray-900">{stats.total_appointments}</div>
              <div className="text-gray-500 text-sm">موعد</div>
            </div>
          </div>

          {/* Channels */}
          {stats.channels && Object.keys(stats.channels).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="font-semibold text-gray-900 mb-4">📱 المحادثات حسب القناة</h2>
              <div className="space-y-3">
                {Object.entries(stats.channels).map(([channel, count]) => (
                  <div key={channel} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span>{channelEmoji[channel] || '📱'}</span>
                      <span className="text-gray-700">{channel}</span>
                    </div>
                    <span className="font-semibold text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Intents */}
          {stats.top_intents && Object.keys(stats.top_intents).length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-5">
              <h2 className="font-semibold text-gray-900 mb-4">🎯 أكثر النوايا شيوعاً</h2>
              <div className="space-y-3">
                {Object.entries(stats.top_intents).map(([intent, count]) => (
                  <div key={intent} className="flex items-center justify-between">
                    <span className="text-gray-700">{intent}</span>
                    <span className="font-semibold text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!stats && (
        <div className="text-center py-12 text-gray-500">
          لا توجد إحصائيات متاحة
        </div>
      )}
    </div>
  )
}
