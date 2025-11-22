'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSearchParams } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Nav from '@/components/Nav'
import toast from 'react-hot-toast'
import ResultPage from '@/components/ResultPage'

const QUESTIONS = [
  'Over the last 2 weeks, how often have you felt down, depressed, or hopeless?',
  'How often have you felt little interest or pleasure in doing things?',
  'How often have you had trouble falling asleep or sleeping too much?',
  'How often have you felt anxious or worried?',
  'How often have you had trouble concentrating on tasks?',
  'How often have you felt tired or had little energy?',
  'Have you had thoughts that you would be better off dead or of hurting yourself?',
  'How often have your feelings interfered with daily life (study, social)?',
]

const OPTIONS = [
  { value: 0, label: 'Not at all' },
  { value: 1, label: 'Several days' },
  { value: 2, label: 'More than half the days' },
  { value: 3, label: 'Nearly every day' },
]

export default function QuestionnairePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const isGuest = searchParams.get('guest') === 'true'
  const { isAuthenticated } = useAuthStore()
  const [currentStep, setCurrentStep] = useState(0)
  const [responses, setResponses] = useState<Record<string, number>>({})
  const [freeText, setFreeText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  useEffect(() => {
    if (!isGuest && !isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isGuest, router])

  const handleSubmit = async () => {
    if (currentStep < QUESTIONS.length) {
      toast.error('Please answer all questions')
      return
    }

    setLoading(true)

    try {
      const response = await api.post('/api/predictions/questionnaire', {
        q1: responses.q1 || 0,
        q2: responses.q2 || 0,
        q3: responses.q3 || 0,
        q4: responses.q4 || 0,
        q5: responses.q5 || 0,
        q6: responses.q6 || 0,
        q7: responses.q7 || 0,
        q8: responses.q8 || 0,
        free_text: freeText,
      })

      setResult(response.data)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to get prediction')
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return <ResultPage result={result} />
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {!isGuest && <Nav />}
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card">
          <div className="mb-6">
            <h1 className="text-3xl font-display font-bold text-primary-700 mb-2">
              Mental Health Assessment
            </h1>
            <p className="text-gray-600">
              Question {currentStep + 1} of {QUESTIONS.length + 1}
            </p>
            <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentStep + 1) / (QUESTIONS.length + 1)) * 100}%` }}
              />
            </div>
          </div>

          {currentStep < QUESTIONS.length ? (
            <div>
              <h2 className="text-xl font-semibold mb-6">{QUESTIONS[currentStep]}</h2>
              <div className="space-y-3">
                {OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => {
                      setResponses({ ...responses, [`q${currentStep + 1}`]: option.value })
                      setTimeout(() => setCurrentStep(currentStep + 1), 200)
                    }}
                    className="w-full text-left px-6 py-4 rounded-xl border-2 border-gray-200 hover:border-primary-500 hover:bg-primary-50 transition-all"
                  >
                    <span className="font-medium">{option.label}</span>
                  </button>
                ))}
              </div>
              <div className="mt-6 flex gap-4">
                {currentStep > 0 && (
                  <button
                    onClick={() => setCurrentStep(currentStep - 1)}
                    className="btn-secondary"
                  >
                    Previous
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div>
              <h2 className="text-xl font-semibold mb-4">Additional Comments (Optional)</h2>
              <textarea
                value={freeText}
                onChange={(e) => setFreeText(e.target.value)}
                className="input-field h-32"
                placeholder="Share any additional thoughts or feelings..."
              />
              <div className="mt-6 flex gap-4">
                <button onClick={() => setCurrentStep(currentStep - 1)} className="btn-secondary">
                  Previous
                </button>
                <button onClick={handleSubmit} disabled={loading} className="btn-primary">
                  {loading ? 'Processing...' : 'Submit Assessment'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 card bg-yellow-50 border-yellow-200">
          <p className="text-sm text-yellow-800">
            <strong>Disclaimer:</strong> This assessment is not a replacement for professional
            mental health care. If you're experiencing a crisis, please contact emergency
            services immediately.
          </p>
        </div>
      </div>
    </div>
  )
}

