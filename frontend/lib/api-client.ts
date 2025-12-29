/**
 * API client wrapper for backend API calls
 */
let API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'clinic-admin-secure-key-2024'

// إذا كان API_BASE اسم خدمة فقط (بدون https://)، أضف https:// و .onrender.com
if (API_BASE && !API_BASE.startsWith('http://') && !API_BASE.startsWith('https://')) {
  API_BASE = `https://${API_BASE}.onrender.com`
}

async function fetchAPI(endpoint: string, options?: RequestInit, requiresAuth: boolean = false) {
  try {
    const url = `${API_BASE}${endpoint}`
    console.log('API Request:', url, options)
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options?.headers,
    }
    
    // إضافة API key للـ admin endpoints
    if (requiresAuth && API_KEY) {
      headers['X-API-Key'] = API_KEY
    }
    
    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const errorText = await response.text()
      let errorMessage = 'حدث خطأ غير متوقع'
      
      try {
        const errorJson = JSON.parse(errorText)
        errorMessage = errorJson.detail || errorJson.message || errorMessage
      } catch {
        errorMessage = errorText || `HTTP ${response.status}: ${response.statusText}`
      }
      
      throw new Error(errorMessage)
    }

    return await response.json()
  } catch (error) {
    console.error('API Error:', error)
    
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('لا يمكن الاتصال بالخادم. تأكد من أن الباك إند يعمل على http://localhost:8000')
    }
    
    if (error instanceof Error) {
      throw error
    }
    
    throw new Error('حدث خطأ غير متوقع')
  }
}

// Analytics
export async function getAnalyticsSummary(from: string, to: string) {
  return fetchAPI(`/admin/analytics/summary?from=${from}&to=${to}`, {}, true)
}

export async function getAnalyticsByChannel(from: string, to: string, channel?: string) {
  const url = channel 
    ? `/admin/analytics/by-channel?from=${from}&to=${to}&channel=${channel}`
    : `/admin/analytics/by-channel?from=${from}&to=${to}`
  return fetchAPI(url, {}, true)
}

// Reports
export async function getDailyReport(date: string) {
  return fetchAPI(`/reports/daily/?date=${date}`)
}

// RAG
export async function getRagSources() {
  return fetchAPI('/admin/rag/sources', {}, true)
}

export async function createRagSource(body: {
  title: string
  source_type: string
  tags?: string
  language?: string
}) {
  return fetchAPI('/admin/rag/sources', {
    method: 'POST',
    body: JSON.stringify(body),
  }, true)
}

export async function ingestRagSourceFile(sourceId: string, file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const headers: HeadersInit = {}
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY
  }

  const response = await fetch(`${API_BASE}/admin/rag/sources/${sourceId}/ingest`, {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'حدث خطأ غير متوقع' }))
    throw new Error(error.message || 'حدث خطأ غير متوقع')
  }

  return await response.json()
}


// Branches
export async function getBranches() {
  return fetchAPI('/admin/branches', {}, true)
}

export async function createBranch(data: any) {
  return fetchAPI('/admin/branches', {
    method: 'POST',
    body: JSON.stringify(data),
  }, true)
}

// Doctors
export async function getDoctors() {
  return fetchAPI('/admin/doctors', {}, true)
}

export async function createDoctor(data: any) {
  return fetchAPI('/admin/doctors', {
    method: 'POST',
    body: JSON.stringify(data),
  }, true)
}

// Services
export async function getServices() {
  return fetchAPI('/admin/services', {}, true)
}

export async function createService(data: any) {
  return fetchAPI('/admin/services', {
    method: 'POST',
    body: JSON.stringify(data),
  }, true)
}

// Offers
export async function getOffers() {
  return fetchAPI('/admin/offers', {}, true)
}

export async function createOffer(data: any) {
  return fetchAPI('/admin/offers', {
    method: 'POST',
    body: JSON.stringify(data),
  }, true)
}

// FAQs
export async function getFaqs() {
  return fetchAPI('/admin/faqs', {}, true)
}

export async function createFaq(data: any) {
  return fetchAPI('/admin/faqs', {
    method: 'POST',
    body: JSON.stringify(data),
  }, true)
}

// Appointments
export async function getAppointments() {
  return fetchAPI('/admin/appointments', {}, true)
}

export async function createAppointment(data: any) {
  return fetchAPI('/admin/appointments', {
    method: 'POST',
    body: JSON.stringify(data),
  }, true)
}

// Test Chat
export async function testChat(message: string, userId: string = 'test_user', channel: string = 'whatsapp') {
  return fetchAPI('/test/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      user_id: userId,
      channel: channel
    }),
  })
}


// Database Management
export async function initDatabase() {
  return fetchAPI('/admin/db/init', {
    method: 'POST',
  }, true)
}

export async function cleanDatabase() {
  return fetchAPI('/admin/db/clean', {
    method: 'POST',
  }, true)
}

export async function dropAllTables() {
  return fetchAPI('/admin/db/drop-all-tables', {
    method: 'POST',
  }, true)
}

export async function addSampleData() {
  return fetchAPI('/admin/db/add-sample-data', {
    method: 'POST',
  }, true)
}

export async function addNorthBranchData() {
  return fetchAPI('/admin/db/add-north-branch-data', {
    method: 'POST',
  }, true)
}

export async function createCoreTables() {
  return fetchAPI('/admin/db/create-core-tables', {
    method: 'POST',
  }, true)
}

export async function addCustomData(data: any) {
  return fetchAPI('/admin/db/add-custom-data', {
    method: 'POST',
    body: JSON.stringify(data),
  }, true)
}

export async function importFromCSV(branchesFile?: File, doctorsFile?: File, servicesFile?: File) {
  const formData = new FormData()
  
  if (branchesFile) {
    formData.append('branches_file', branchesFile)
  }
  if (doctorsFile) {
    formData.append('doctors_file', doctorsFile)
  }
  if (servicesFile) {
    formData.append('services_file', servicesFile)
  }

  const headers: HeadersInit = {}
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY
  }

  const response = await fetch(`${API_BASE}/admin/csv-import/import-from-csv', {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'حدث خطأ غير متوقع' }))
    throw new Error(error.detail || error.message || 'حدث خطأ غير متوقع')
  }

  return await response.json()
}



