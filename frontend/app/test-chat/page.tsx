"use client"

import { useState, useRef, useEffect } from 'react'
import { testChat, initDatabase } from '../../lib/api-client'

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
  const [initializingDB, setInitializingDB] = useState(false)
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
            <div className="flex gap-3">
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
