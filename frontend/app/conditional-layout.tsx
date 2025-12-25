"use client"

import { usePathname } from 'next/navigation'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Sidebar from '../components/Sidebar'
import Topbar from '../components/Topbar'

export default function ConditionalLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const router = useRouter()

  // إعادة توجيه الصفحة الرئيسية إلى الإحصائيات
  useEffect(() => {
    if (pathname === '/') {
      router.replace('/analytics')
    }
  }, [pathname, router])

  // Dashboard layout with sidebar and topbar
  return (
    <div className="flex h-full bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden pr-0 transition-all duration-300 sm:pr-64">
        <Topbar />
        <main className="flex-1 overflow-y-auto bg-gray-50">
          {pathname === '/test-chat' ? (
            children
          ) : (
            <div className="p-6">
              {children}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}


