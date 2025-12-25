/**
 * Form Validation Schemas using simple validation (no external library needed)
 */

export interface ValidationError {
  field: string
  message: string
}

export function validateEmail(email: string): ValidationError | null {
  if (!email) {
    return { field: 'email', message: 'البريد الإلكتروني مطلوب' }
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    return { field: 'email', message: 'البريد الإلكتروني غير صحيح' }
  }
  return null
}

export function validateRequired(value: any, fieldName: string): ValidationError | null {
  if (!value || (typeof value === 'string' && value.trim() === '')) {
    return { field: fieldName, message: `${fieldName} مطلوب` }
  }
  return null
}

export function validatePhone(phone: string): ValidationError | null {
  if (!phone) {
    return { field: 'phone', message: 'رقم الهاتف مطلوب' }
  }
  // رقم هاتف سعودي: يبدأ بـ 05 أو 966
  const phoneRegex = /^(05|966)[0-9]{8,9}$/
  if (!phoneRegex.test(phone.replace(/\s+/g, ''))) {
    return { field: 'phone', message: 'رقم الهاتف غير صحيح (يجب أن يكون رقم سعودي)' }
  }
  return null
}

export function validateLength(
  value: string,
  min: number,
  max: number,
  fieldName: string
): ValidationError | null {
  if (value.length < min) {
    return { field: fieldName, message: `${fieldName} يجب أن يكون على الأقل ${min} حرف` }
  }
  if (value.length > max) {
    return { field: fieldName, message: `${fieldName} يجب أن يكون على الأكثر ${max} حرف` }
  }
  return null
}

export function validateBranch(data: {
  name: string
  city: string
  address: string
  phone?: string
}): ValidationError[] {
  const errors: ValidationError[] = []

  const nameError = validateRequired(data.name, 'اسم الفرع')
  if (nameError) errors.push(nameError)

  const cityError = validateRequired(data.city, 'المدينة')
  if (cityError) errors.push(cityError)

  const addressError = validateRequired(data.address, 'العنوان')
  if (addressError) errors.push(addressError)

  if (data.phone) {
    const phoneError = validatePhone(data.phone)
    if (phoneError) errors.push(phoneError)
  }

  return errors
}

export function validateDoctor(data: {
  name: string
  specialty: string
  branch_id: string
}): ValidationError[] {
  const errors: ValidationError[] = []

  const nameError = validateRequired(data.name, 'اسم الطبيب')
  if (nameError) errors.push(nameError)

  const specialtyError = validateRequired(data.specialty, 'التخصص')
  if (specialtyError) errors.push(specialtyError)

  const branchError = validateRequired(data.branch_id, 'الفرع')
  if (branchError) errors.push(branchError)

  return errors
}

export function validateService(data: {
  name: string
  description?: string
  base_price?: number
}): ValidationError[] {
  const errors: ValidationError[] = []

  const nameError = validateRequired(data.name, 'اسم الخدمة')
  if (nameError) errors.push(nameError)

  if (data.base_price !== undefined && data.base_price < 0) {
    errors.push({ field: 'base_price', message: 'السعر يجب أن يكون أكبر من أو يساوي صفر' })
  }

  return errors
}

export function validateFAQ(data: {
  question: string
  answer: string
}): ValidationError[] {
  const errors: ValidationError[] = []

  const questionError = validateRequired(data.question, 'السؤال')
  if (questionError) errors.push(questionError)

  const answerError = validateRequired(data.answer, 'الجواب')
  if (answerError) errors.push(answerError)

  return errors
}

export function validateAppointment(data: {
  patient_name: string
  phone: string
  branch_id: string
  service_id: string
  datetime: string
}): ValidationError[] {
  const errors: ValidationError[] = []

  const nameError = validateRequired(data.patient_name, 'اسم المريض')
  if (nameError) errors.push(nameError)

  const phoneError = validatePhone(data.phone)
  if (phoneError) errors.push(phoneError)

  const branchError = validateRequired(data.branch_id, 'الفرع')
  if (branchError) errors.push(branchError)

  const serviceError = validateRequired(data.service_id, 'الخدمة')
  if (serviceError) errors.push(serviceError)

  const datetimeError = validateRequired(data.datetime, 'تاريخ ووقت الموعد')
  if (datetimeError) errors.push(datetimeError)

  // التحقق من أن التاريخ في المستقبل
  if (data.datetime) {
    const appointmentDate = new Date(data.datetime)
    const now = new Date()
    if (appointmentDate <= now) {
      errors.push({ field: 'datetime', message: 'تاريخ الموعد يجب أن يكون في المستقبل' })
    }
  }

  return errors
}

