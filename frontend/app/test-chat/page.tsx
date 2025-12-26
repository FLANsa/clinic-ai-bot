"use client"

import { useState, useRef, useEffect } from 'react'
import { testChat, cleanDatabase, initDatabase, addSampleData, testWhatsAppConnection, sendWhatsAppTestMessage, diagnoseBotIssues, DiagnosticResponse } from '../../lib/api-client'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  intent?: string
  metadata?: {
    rag_used?: boolean
    unrecognized?: boolean
    needs_handoff?: boolean
  }
}

export default function TestChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedChannel, setSelectedChannel] = useState<string>('whatsapp')
  const [cleaningDB, setCleaningDB] = useState(false)
  const [initializingDB, setInitializingDB] = useState(false)
  const [addingSampleData, setAddingSampleData] = useState(false)
  const [testingWhatsApp, setTestingWhatsApp] = useState(false)
  const [whatsappTestResult, setWhatsappTestResult] = useState<any>(null)
  const [showTestMessage, setShowTestMessage] = useState(false)
  const [testPhoneNumber, setTestPhoneNumber] = useState('')
  const [testMessage, setTestMessage] = useState('رسالة تجريبية من عيادة - هذا اختبار للتحقق من ربط WhatsApp API')
  const [sendingTestMessage, setSendingTestMessage] = useState(false)
  const [diagnosing, setDiagnosing] = useState(false)
  const [diagnosticResult, setDiagnosticResult] = useState<DiagnosticResponse | null>(null)
  const [showDiagnostic, setShowDiagnostic] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  // استخدام user_id ثابت لكل جلسة الاختبار (لكل قناة منفصلة)
  const userIdRef = useRef<Record<string, string>>({})
  
  // إنشاء user_id لكل قناة
  const getUserIdForChannel = (channel: string): string => {
    if (!userIdRef.current[channel]) {
      userIdRef.current[channel] = `test_user_${channel}_${Date.now()}`
    }
    return userIdRef.current[channel]
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!inputMessage.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setLoading(true)
    setError(null)

    try {
      const userId = getUserIdForChannel(selectedChannel)
      const response = await testChat(userMessage.content, userId, selectedChannel)
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        intent: response.intent || undefined,
        metadata: {
          rag_used: response.rag_used,
          unrecognized: response.unrecognized,
          needs_handoff: response.needs_handoff
        }
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ غير متوقع')
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'عذراً، حدث خطأ في الاتصال بالبوت. تأكد من تشغيل الخادم على البورت 8000.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearChat = () => {
    setMessages([])
    setError(null)
    // إعادة تعيين user_id للقناة الحالية لبدء محادثة جديدة
    if (userIdRef.current[selectedChannel]) {
      userIdRef.current[selectedChannel] = `test_user_${selectedChannel}_${Date.now()}`
    }
  }

  const handleCleanDatabase = async () => {
    if (!confirm('⚠️ هل أنت متأكد من حذف جميع البيانات من قاعدة البيانات؟\n\nهذه العملية لا يمكن التراجع عنها!')) {
      return
    }

    setCleaningDB(true)
    setError(null)

    try {
      const result = await cleanDatabase()
      alert(`✅ تم تنظيف قاعدة البيانات بنجاح!\n\nتم حذف:\n${Object.entries(result.deleted_counts || {})
        .map(([key, value]) => `- ${key}: ${value}`)
        .join('\n')}`)
      
      // مسح المحادثة أيضاً بعد تنظيف قاعدة البيانات
      clearChat()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ أثناء تنظيف قاعدة البيانات')
      alert(`❌ خطأ: ${err instanceof Error ? err.message : 'حدث خطأ غير متوقع'}`)
    } finally {
      setCleaningDB(false)
    }
  }

  const handleInitDatabase = async () => {
    if (!confirm('هل تريد تهيئة قاعدة البيانات؟\n\nسيتم إنشاء جميع الجداول والـ indexes المطلوبة.')) {
      return
    }

    setInitializingDB(true)
    setError(null)

    try {
      const result = await initDatabase()
      alert(`✅ تم تهيئة قاعدة البيانات بنجاح!\n\n${result.message || 'تم إنشاء جميع الجداول بنجاح'}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ أثناء تهيئة قاعدة البيانات')
      alert(`❌ خطأ: ${err instanceof Error ? err.message : 'حدث خطأ غير متوقع'}`)
    } finally {
      setInitializingDB(false)
    }
  }

  const handleAddSampleData = async () => {
    if (!confirm('هل تريد إضافة بيانات تجريبية؟\n\nسيتم إضافة فروع، أطباء، خدمات، عروض، وأسئلة شائعة.')) {
      return
    }

    setAddingSampleData(true)
    setError(null)

    try {
      const result = await addSampleData()
      const counts = result.details?.counts || {}
      const countsText = Object.entries(counts)
        .map(([key, value]) => `- ${key}: ${value}`)
        .join('\n')
      alert(`✅ تم إضافة البيانات التجريبية بنجاح!\n\n${result.message}\n\nالبيانات المضافة:\n${countsText}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ أثناء إضافة البيانات التجريبية')
      alert(`❌ خطأ: ${err instanceof Error ? err.message : 'حدث خطأ غير متوقع'}`)
    } finally {
      setAddingSampleData(false)
    }
  }

  const handleTestWhatsApp = async () => {
    setTestingWhatsApp(true)
    setWhatsappTestResult(null)
    setError(null)

    try {
      const result = await testWhatsAppConnection()
      setWhatsappTestResult(result)
      
      if (result.success) {
        setShowTestMessage(true)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ أثناء اختبار WhatsApp')
      setWhatsappTestResult({
        success: false,
        message: err instanceof Error ? err.message : 'حدث خطأ غير متوقع'
      })
    } finally {
      setTestingWhatsApp(false)
    }
  }

  const handleSendTestMessage = async () => {
    if (!testPhoneNumber.trim()) {
      alert('⚠️ يرجى إدخال رقم الهاتف')
      return
    }

    setSendingTestMessage(true)
    setError(null)

    try {
      const result = await sendWhatsAppTestMessage(testPhoneNumber.trim(), testMessage)
      if (result.success) {
        alert(`✅ ${result.message}`)
        setShowTestMessage(false)
        setTestPhoneNumber('')
      } else {
        alert(`❌ ${result.message}`)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ أثناء إرسال الرسالة')
      alert(`❌ خطأ: ${err instanceof Error ? err.message : 'حدث خطأ غير متوقع'}`)
    } finally {
      setSendingTestMessage(false)
    }
  }

  const handleDiagnose = async () => {
    setDiagnosing(true)
    setDiagnosticResult(null)
    setShowDiagnostic(true)
    setError(null)

    try {
      const result = await diagnoseBotIssues('مرحبا')
      setDiagnosticResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'حدث خطأ أثناء التشخيص')
      setDiagnosticResult({
        overall_status: 'unhealthy',
        results: [{
          component: 'diagnostic_error',
          status: 'error',
          message: err instanceof Error ? err.message : 'حدث خطأ غير متوقع'
        }],
        recommendations: ['تحقق من اتصال الخادم']
      })
    } finally {
      setDiagnosing(false)
    }
  }
  
  // تحديث الرسائل عند تغيير القناة (لكل قناة محادثة منفصلة)
  useEffect(() => {
    setMessages([])
    setError(null)
  }, [selectedChannel])

  return (
    <div className="h-full bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-white to-gray-50 shadow-md border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6 py-5">
          <div className="flex justify-between items-center mb-5">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-1">
                اختبار الشات بوت
              </h1>
              <p className="text-sm text-gray-600">اختبر ردود البوت على جميع القنوات</p>
            </div>
            <div className="flex gap-3 flex-wrap">
              <button
                onClick={clearChat}
                className="btn-secondary flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                مسح المحادثة
              </button>
              <button
                onClick={handleInitDatabase}
                disabled={initializingDB}
                className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors duration-200"
              >
                {initializingDB ? (
                  <>
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    جاري التهيئة...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    تهيئة قاعدة البيانات
                  </>
                )}
              </button>
              <button
                onClick={handleAddSampleData}
                disabled={addingSampleData}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors duration-200"
              >
                {addingSampleData ? (
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
                    إضافة بيانات تجريبية
                  </>
                )}
              </button>
              <button
                onClick={handleTestWhatsApp}
                disabled={testingWhatsApp}
                className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors duration-200"
              >
                {testingWhatsApp ? (
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
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    اختبار ربط WhatsApp
                  </>
                )}
              </button>
              <button
                onClick={handleCleanDatabase}
                disabled={cleaningDB}
                className="bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors duration-200"
              >
                {cleaningDB ? (
                  <>
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    جاري التنظيف...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    تنظيف قاعدة البيانات
                  </>
                )}
              </button>
              <button
                onClick={handleDiagnose}
                disabled={diagnosing}
                className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors duration-200"
              >
                {diagnosing ? (
                  <>
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    جاري التشخيص...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                    </svg>
                    🔍 تشخيص المشاكل
                  </>
                )}
              </button>
            </div>
          </div>
          
          {/* Channel Selector */}
          <div className="border-t border-gray-200 pt-5">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              اختر القناة للاختبار:
            </label>
            <div className="flex gap-3 flex-wrap">
              {[
                { id: 'whatsapp', label: 'واتساب', icon: '💬', color: 'from-green-500 to-green-600' },
                { id: 'instagram', label: 'إنستقرام', icon: '📷', color: 'from-pink-500 to-rose-600' },
                { id: 'google_maps', label: 'جوجل ماب', icon: '🗺️', color: 'from-red-500 to-red-600' },
                { id: 'tiktok', label: 'تيك توك', icon: '🎵', color: 'from-gray-800 to-black' }
              ].map((channel) => (
                <button
                  key={channel.id}
                  onClick={() => setSelectedChannel(channel.id)}
                  className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
                    selectedChannel === channel.id
                      ? `bg-gradient-to-r ${channel.color} text-white shadow-lg transform scale-105`
                      : 'bg-white border-2 border-gray-200 text-gray-700 hover:border-gray-300 hover:shadow-md'
                  }`}
                >
                  <span className="mr-2">{channel.icon}</span>
                  {channel.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-3 flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              كل قناة لها محادثة منفصلة - سيتم حفظ السياق حسب القناة المختارة
            </p>
          </div>

          {/* WhatsApp Test Result */}
          {whatsappTestResult && (
            <div className={`mt-5 p-4 rounded-lg border-2 ${
              whatsappTestResult.success 
                ? 'bg-green-50 border-green-200' 
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-start gap-3">
                <div className={`text-2xl ${whatsappTestResult.success ? 'text-green-600' : 'text-red-600'}`}>
                  {whatsappTestResult.success ? '✅' : '❌'}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 mb-1">
                    {whatsappTestResult.success ? 'نجح الاختبار' : 'فشل الاختبار'}
                  </h3>
                  <p className="text-sm text-gray-700 mb-2 whitespace-pre-line">{whatsappTestResult.message}</p>
                  {whatsappTestResult.details && (
                    <div className="mt-2 text-xs text-gray-600">
                      {whatsappTestResult.details.credentials && (
                        <div className="mb-2">
                          <strong>البيانات:</strong>
                          <ul className="list-disc list-inside ml-2 mt-1">
                            <li>Access Token: {whatsappTestResult.details.credentials.access_token}</li>
                            <li>Phone Number ID: {whatsappTestResult.details.credentials.phone_number_id}</li>
                          </ul>
                        </div>
                      )}
                      {whatsappTestResult.details.api_connection && (
                        <div>
                          <strong>الاتصال:</strong> {whatsappTestResult.details.api_connection.status}
                          {whatsappTestResult.details.api_connection.error && (
                            <div className="mt-1 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-800">
                              <strong>الخطأ:</strong> {whatsappTestResult.details.api_connection.error}
                              {whatsappTestResult.details.api_connection.solution && (
                                <div className="mt-1"><strong>الحل:</strong> {whatsappTestResult.details.api_connection.solution}</div>
                              )}
                            </div>
                          )}
                          {whatsappTestResult.details.api_connection.phone_number_info && (
                            <ul className="list-disc list-inside ml-2 mt-1">
                              <li>رقم العرض: {whatsappTestResult.details.api_connection.phone_number_info.display_phone_number || 'غير متوفر'}</li>
                              <li>الاسم المؤكد: {whatsappTestResult.details.api_connection.phone_number_info.verified_name || 'غير متوفر'}</li>
                            </ul>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Diagnostic Results */}
          {showDiagnostic && diagnosticResult && (
            <div className={`mt-5 p-4 rounded-lg border-2 ${
              diagnosticResult.overall_status === 'healthy'
                ? 'bg-green-50 border-green-200'
                : diagnosticResult.overall_status === 'degraded'
                ? 'bg-yellow-50 border-yellow-200'
                : 'bg-red-50 border-red-200'
            }`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`text-2xl ${
                    diagnosticResult.overall_status === 'healthy' ? 'text-green-600' :
                    diagnosticResult.overall_status === 'degraded' ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {diagnosticResult.overall_status === 'healthy' ? '✅' :
                     diagnosticResult.overall_status === 'degraded' ? '⚠️' :
                     '❌'}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      نتائج التشخيص: {
                        diagnosticResult.overall_status === 'healthy' ? 'كل شيء يعمل بشكل صحيح' :
                        diagnosticResult.overall_status === 'degraded' ? 'بعض الأنظمة تحتاج انتباه' :
                        'هناك مشاكل خطيرة'
                      }
                    </h3>
                    <p className="text-sm text-gray-600">
                      تم فحص {diagnosticResult.results.length} مكون
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowDiagnostic(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-3 mt-4">
                {diagnosticResult.results.map((result, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${
                      result.status === 'ok' ? 'bg-white border-green-200' :
                      result.status === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                      'bg-red-50 border-red-200'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <span className={`text-lg ${
                        result.status === 'ok' ? 'text-green-600' :
                        result.status === 'warning' ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {result.status === 'ok' ? '✅' :
                         result.status === 'warning' ? '⚠️' :
                         '❌'}
                      </span>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 mb-1">
                          {result.component === 'database_data' ? 'قاعدة البيانات' :
                           result.component === 'db_context_loading' ? 'جلب السياق من قاعدة البيانات' :
                           result.component === 'llm_connection' ? 'اتصال LLM' :
                           result.component === 'message_handling' ? 'معالجة الرسائل' :
                           result.component}
                        </h4>
                        <p className="text-sm text-gray-700 mb-2">{result.message}</p>
                        {result.error_type && (
                          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
                            <strong>نوع الخطأ:</strong> {result.error_type}<br/>
                            <strong>الرسالة:</strong> {result.error_message}
                          </div>
                        )}
                        {result.details && Object.keys(result.details).length > 0 && (
                          <div className="mt-2 text-xs text-gray-600">
                            <strong>التفاصيل:</strong>
                            <ul className="list-disc list-inside ml-2 mt-1">
                              {Object.entries(result.details).map(([key, value]) => (
                                <li key={key}>{key}: {String(value)}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {diagnosticResult.recommendations && diagnosticResult.recommendations.length > 0 && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <h4 className="font-semibold text-blue-900 mb-2">💡 التوصيات:</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-blue-800">
                    {diagnosticResult.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Send Test Message Form */}
          {showTestMessage && whatsappTestResult?.success && (
            <div className="mt-5 p-4 bg-blue-50 border-2 border-blue-200 rounded-lg">
              <h3 className="font-semibold text-gray-900 mb-3">إرسال رسالة تجريبية</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    رقم الهاتف (مع رمز البلد، مثال: 966501234567)
                  </label>
                  <input
                    type="text"
                    value={testPhoneNumber}
                    onChange={(e) => setTestPhoneNumber(e.target.value)}
                    placeholder="966501234567"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    نص الرسالة
                  </label>
                  <textarea
                    value={testMessage}
                    onChange={(e) => setTestMessage(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleSendTestMessage}
                    disabled={sendingTestMessage || !testPhoneNumber.trim()}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors duration-200"
                  >
                    {sendingTestMessage ? (
                      <>
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        جاري الإرسال...
                      </>
                    ) : (
                      <>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                        إرسال الرسالة
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setShowTestMessage(false)
                      setTestPhoneNumber('')
                    }}
                    className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg font-semibold transition-colors duration-200"
                  >
                    إلغاء
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 min-h-0">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-16">
              <div className="inline-block p-6 bg-gradient-to-br from-blue-100 to-purple-100 rounded-2xl mb-6 shadow-lg">
                <span className="text-5xl">💬</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">ابدأ المحادثة</h2>
              <p className="text-gray-600 mb-6">اكتب رسالة لاختبار ردود البوت</p>
              <div className="mt-8">
                <p className="font-semibold text-gray-700 mb-3">أمثلة للأسئلة:</p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {['السلام عليكم', 'ايش هي خدماتكم؟', 'مين الاطباء الي عندكم؟', 'وين موقعكم؟', 'ابي احجز موعد'].map((example, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputMessage(example)}
                      className="px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700 transition-all duration-200"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-5 py-4 shadow-md ${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
                    : 'bg-white border-2 border-gray-200 text-gray-900'
                }`}
              >
                <div className="whitespace-pre-wrap break-words leading-relaxed">{message.content}</div>
                {message.metadata && (
                  <div className="mt-3 pt-3 border-t border-opacity-20 text-xs">
                    {message.intent && (
                      <div className="mb-2 font-semibold opacity-90">
                        النية: <span className="font-normal">{message.intent}</span>
                      </div>
                    )}
                    <div className="flex gap-2 flex-wrap">
                      {message.metadata.rag_used && (
                        <span className="badge badge-info">RAG</span>
                      )}
                      {message.metadata.unrecognized && (
                        <span className="badge badge-warning">غير مفهوم</span>
                      )}
                      {message.metadata.needs_handoff && (
                        <span className="badge badge-error">يحتاج تحويل</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start mb-4">
              <div className="bg-white border-2 border-gray-200 rounded-2xl px-5 py-4 shadow-md">
                <div className="flex items-center gap-3 text-gray-600">
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="font-medium">جاري المعالجة...</span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border-2 border-red-200 rounded-2xl px-5 py-4 text-red-800 shadow-md mb-4">
              <div className="flex items-start gap-3">
                <svg className="w-6 h-6 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="font-bold mb-1">خطأ</p>
                  <p>{error}</p>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-gradient-to-r from-white to-gray-50 border-t-2 border-gray-200 shadow-lg px-6 py-5">
        <div className="max-w-5xl mx-auto">
          <div className="flex gap-3">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="اكتب رسالتك هنا..."
              disabled={loading}
              className="input-field flex-1 text-base"
            />
            <button
              onClick={handleSend}
              disabled={loading || !inputMessage.trim()}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              إرسال
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-3 text-center flex items-center justify-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-xs">Enter</kbd>
              للإرسال
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-xs">Shift+Enter</kbd>
              للسطر الجديد
            </span>
          </p>
        </div>
      </div>
    </div>
  )
}
