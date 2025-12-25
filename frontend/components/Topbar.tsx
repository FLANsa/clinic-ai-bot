"use client"

export default function Topbar() {
  return (
    <div className="bg-gradient-to-r from-white to-gray-50 shadow-md border-b border-gray-200 px-6 py-4 z-20 relative">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
            <span className="text-white font-bold text-lg">AI</span>
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              نظام إدارة العيادة
            </h1>
            <p className="text-xs text-gray-500">AI Chat Bot Management</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-blue-700">نشط</span>
          </div>
        </div>
      </div>
    </div>
  )
}

