import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout (increased for slow operations)
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth-storage')
  if (token) {
    try {
      const parsed = JSON.parse(token)
      if (parsed.state?.token) {
        config.headers.Authorization = `Bearer ${parsed.state.token}`
      }
    } catch (e) {
      // Ignore parse errors
    }
  }
  // Don't set Content-Type for FormData - let browser set it with boundary
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-storage')
      window.location.href = '/auth/login'
    }
    return Promise.reject(error)
  }
)

// Therapist API functions
export const therapistApi = {
  startSession: async () => {
    const response = await api.post('/api/therapist/start')
    return response.data
  },
  
  submitAnswers: async (sessionId: string, answers: any[]) => {
    const response = await api.post('/api/therapist/answer', {
      session_id: sessionId,
      answers
    })
    return response.data
  },
  
  getFinalPlan: async (sessionId: string) => {
    const response = await api.post(`/api/therapist/final-plan?session_id=${sessionId}`)
    return response.data
  }
}

