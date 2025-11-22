'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Link from 'next/link'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const router = useRouter()
  const { setAuth } = useAuthStore()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    university: '',
    consent_given: false,
  })
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.consent_given) {
      toast.error('You must agree to the terms and conditions')
      return
    }

    setLoading(true)

    try {
      const response = await api.post('/api/auth/register', formData)
      const { id, email, is_admin, university } = response.data

      // Login after registration
      const loginFormData = new FormData()
      loginFormData.append('username', formData.email)
      loginFormData.append('password', formData.password)

      const loginResponse = await api.post('/api/auth/login', loginFormData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setAuth({ id, email, is_admin, university }, loginResponse.data.access_token)
      toast.success('Registration successful!')
      router.push('/dashboard')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-accent-50 p-4">
      <div className="card w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-display font-bold text-primary-700 mb-2">
            Create Account
          </h1>
          <p className="text-gray-600">Sign up to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="input-field"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="input-field"
              required
              minLength={6}
            />
          </div>

          <div>
            <label htmlFor="university" className="block text-sm font-medium text-gray-700 mb-2">
              University (Optional)
            </label>
            <input
              id="university"
              type="text"
              value={formData.university}
              onChange={(e) => setFormData({ ...formData, university: e.target.value })}
              className="input-field"
            />
          </div>

          <div className="flex items-start">
            <input
              id="consent"
              type="checkbox"
              checked={formData.consent_given}
              onChange={(e) => setFormData({ ...formData, consent_given: e.target.checked })}
              className="mt-1 mr-2"
              required
            />
            <label htmlFor="consent" className="text-sm text-gray-700">
              I agree to the data usage policy and understand this is not a replacement for
              professional mental health care.
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-primary-700 font-semibold hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

