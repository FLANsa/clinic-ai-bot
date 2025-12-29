"use client"

import { useState, useEffect } from 'react'
import { testChat, createCoreTables, addCustomData } from '../../lib/api-client'

interface TestResult {
  name: string
  status: 'success' | 'error' | 'warning' | 'pending'
  message: string
  details?: any
}

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [creatingTables, setCreatingTables] = useState(false)
  const [addingData, setAddingData] = useState(false)

  useEffect(() => {
    setLoading(false)
  }, [])

  const runComprehensiveTests = async () => {
    setTesting(true)
    setTestResults([])

    const results: TestResult[] = []


    // 2. Test Chat
    try {
      results.push({ name: 'اختبار البوت', status: 'pending', message: 'جاري الاختبار...' })
      setTestResults([...results])
      
      const chatResponse = await testChat('السلام عليكم', 'test_user_' + Date.now(), 'whatsapp')
      
      results[results.length - 1] = {
        name: 'اختبار البوت',
        status: 'success',
        message: 'البوت يرد بشكل صحيح',
        details: { reply: chatResponse.reply?.substring(0, 50) + '...' }
      }
      setTestResults([...results])
    } catch (err) {
      results[results.length - 1] = {
        name: 'اختبار البوت',
        status: 'error',
        message: err instanceof Error ? err.message : 'فشل اختبار البوت'
      }
      setTestResults([...results])
    }

    // 3. Test Different Channels
    const channels = ['whatsapp', 'instagram', 'google_maps', 'tiktok']
    for (const channel of channels) {
      try {
        results.push({ name: `اختبار قناة ${channel}`, status: 'pending', message: 'جاري الاختبار...' })
        setTestResults([...results])
        
        const response = await testChat('مرحبا', 'test_user_' + Date.now(), channel)
        
        results[results.length - 1] = {
          name: `اختبار قناة ${channel}`,
          status: 'success',
          message: 'القناة تعمل بشكل صحيح'
        }
        setTestResults([...results])
      } catch (err) {
        results[results.length - 1] = {
          name: `اختبار قناة ${channel}`,
          status: 'error',
          message: err instanceof Error ? err.message : 'فشل اختبار القناة'
        }
        setTestResults([...results])
      }
    }

    setTesting(false)
  }

  const handleCreateCoreTables = async () => {
    if (!confirm('هل تريد إنشاء الجداول الأساسية (branches, doctors, services)؟\n\nسيتم إنشاء الجداول الثلاثة فقط.')) {
      return
    }

    setCreatingTables(true)
    setError(null)

    try {
      const result = await createCoreTables()
      alert(`✅ ${result.message || 'تم إنشاء الجداول بنجاح!'}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ أثناء إنشاء الجداول')
      alert(`❌ خطأ: ${err instanceof Error ? err.message : 'حدث خطأ غير متوقع'}`)
    } finally {
      setCreatingTables(false)
    }
  }

  const handleAddCustomData = async () => {
    // هذا الزر جاهز لاستقبال البيانات
    // سيتم تحديثه بعد أن يوفر المستخدم البيانات
    alert('⚠️ هذا الزر جاهز لاستقبال البيانات.\n\nيرجى توفير البيانات في ملف JSON وسأقوم بتحديث الوظيفة.')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">جاري التحميل...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
        <p className="font-semibold">⚠️ خطأ:</p>
        <p>{error}</p>
      </div>
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return '✅'
      case 'error':
        return '❌'
      case 'warning':
        return '⚠️'
      default:
        return '⏳'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-2">
            لوحة التحكم
          </h1>
          <p className="text-gray-600">نظرة عامة شاملة على أداء البوت والتفاعلات</p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={runComprehensiveTests}
            disabled={testing}
            className="btn-primary flex items-center gap-2"
          >
            {testing ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                جاري الاختبار...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                اختبار شامل للنظام
              </>
            )}
          </button>
          <button
            onClick={handleCreateCoreTables}
            disabled={creatingTables}
            className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors duration-200"
            title="إنشاء جداول branches, doctors, services"
          >
            {creatingTables ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                جاري الإنشاء...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                إنشاء الجداول الأساسية
              </>
            )}
          </button>
          <button
            onClick={handleAddCustomData}
            disabled={addingData}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors duration-200"
            title="إضافة بيانات مخصصة للجداول"
          >
            {addingData ? (
              <>
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                جاري الإضافة...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                إضافة بيانات مخصصة
              </>
            )}
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">إجمالي المحادثات</h3>
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
          </div>
          <p className="text-4xl font-bold text-blue-600 mb-1">-</p>
          <p className="text-sm text-gray-500">جميع المحادثات</p>
        </div>
        
        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">المحادثات اليوم</h3>
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-4xl font-bold text-green-600 mb-1">-</p>
          <p className="text-sm text-gray-500">آخر 24 ساعة</p>
        </div>
        
        <div className="stat-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">متوسط الرضا</h3>
            <div className="p-2 bg-yellow-100 rounded-lg">
              <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            </div>
          </div>
          <p className="text-4xl font-bold text-yellow-600 mb-1">-</p>
          <p className="text-sm text-gray-500">من 5</p>
        </div>
      </div>

      {/* Test Results */}
      {testResults.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 bg-purple-100 rounded-lg">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">نتائج الاختبار الشامل</h2>
              <p className="text-sm text-gray-500">حالة جميع أنظمة البوت</p>
            </div>
          </div>
          <div className="space-y-4">
            {testResults.map((result, index) => (
              <div
                key={index}
                className={`border-2 rounded-xl p-5 transition-all duration-200 hover:shadow-lg ${getStatusColor(result.status)}`}
              >
                <div className="flex items-start gap-4">
                  <div className={`text-3xl ${result.status === 'pending' ? 'animate-pulse' : ''}`}>
                    {getStatusIcon(result.status)}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-lg mb-1">{result.name}</h3>
                    <p className="text-sm mb-3 opacity-90">{result.message}</p>
                    {result.details && (
                      <details className="mt-3">
                        <summary className="cursor-pointer text-sm font-semibold hover:underline">
                          عرض التفاصيل
                        </summary>
                        <div className="mt-3 bg-black/5 dark:bg-white/10 rounded-lg p-4 overflow-auto max-h-60">
                          <pre className="text-xs font-mono">
                            {JSON.stringify(result.details, null, 2)}
                          </pre>
                        </div>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">الإحصائيات التفصيلية</h2>
        <p className="text-gray-600">سيتم إضافة المزيد من الإحصائيات والرسوم البيانية قريباً...</p>
      </div>
    </div>
  )
}

