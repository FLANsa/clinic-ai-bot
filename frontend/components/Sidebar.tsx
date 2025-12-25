"use client"

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Sidebar() {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)

  const menuItems = [
    { href: '/analytics', label: 'الرئيسية / الإحصائيات' },
    { href: '/test-chat', label: '🧪 اختبار البوت', highlight: true },
    { href: '/branches', label: 'الفروع' },
    { href: '/doctors', label: 'الأطباء' },
    { href: '/services', label: 'الخدمات' },
    { href: '/offers', label: 'العروض' },
    { href: '/faq', label: 'الأسئلة الشائعة' },
    { href: '/appointments', label: 'المواعيد' },
    { href: '/reports/daily', label: 'التقارير اليومية' },
    { href: '/knowledge', label: 'المعرفة' },
  ]

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 right-4 z-50 sm:hidden bg-blue-600 text-white p-2 rounded-lg shadow-lg"
        aria-label="Toggle menu"
      >
        {isOpen ? (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 sm:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`w-64 bg-gradient-to-b from-white to-gray-50 shadow-xl border-l border-gray-200 fixed right-0 top-0 h-full overflow-y-auto z-30 transform transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full sm:translate-x-0'
        }`}
        style={{ direction: 'rtl' }}
      >
        <div className="p-5">
          <div className="flex justify-between items-center mb-8 pt-2">
            <h2 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              القائمة
            </h2>
            <button
              onClick={() => setIsOpen(false)}
              className="sm:hidden text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-lg p-1 transition-colors"
              aria-label="Close menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <nav className="space-y-1.5">
            {menuItems.map((item) => {
              const isActive = pathname === item.href
              const highlight = (item as any).highlight
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsOpen(false)}
                  className={`block px-4 py-3 rounded-xl transition-all duration-200 text-sm sm:text-base font-medium ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg shadow-blue-500/30'
                      : highlight
                      ? 'text-blue-700 font-semibold hover:bg-blue-50 border-2 border-blue-200 hover:border-blue-300 hover:shadow-md'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>
      </aside>
    </>
  )
}

