'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Nav from '@/components/Nav'
import toast from 'react-hot-toast'
import ResultPage from '@/components/ResultPage'

export default function TestModelPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [modelInfo, setModelInfo] = useState<any>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, router])

  useEffect(() => {
    // Fetch active model info
    const fetchModelInfo = async () => {
      try {
        const response = await api.get('/api/training/jobs')
        const jobs = response.data
        const completedJob = jobs.find((job: any) => job.status === 'completed' && job.metrics)
        if (completedJob) {
          setModelInfo({
            job_id: completedJob.job_id,
            model_type: completedJob.model_type,
            metrics: completedJob.metrics,
            created_at: completedJob.created_at
          })
        }
      } catch (error) {
        // Model info not critical, continue without it
      }
    }
    fetchModelInfo()
  }, [])

  const handleSubmit = async () => {
    if (!text.trim()) {
      toast.error('Please enter some text to test')
      return
    }

    setLoading(true)
    setResult(null)

    try {
      const response = await api.post('/api/predictions/text', {
        text: text.trim()
      })

      setResult(response.data)
      toast.success('Prediction completed!')
    } catch (error: any) {
      console.error('Prediction error:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to get prediction'
      toast.error(errorMessage)
      // Show more details in console for debugging
      if (error.response) {
        console.error('Response status:', error.response.status)
        console.error('Response data:', error.response.data)
      }
    } finally {
      setLoading(false)
    }
  }

  if (result) {
    return <ResultPage result={result} />
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card mb-6">
          <h1 className="text-3xl font-display font-bold text-primary-700 mb-2">
            Test Your Trained Model
          </h1>
          <p className="text-gray-600">
            Enter text below to test your trained mental health classification model
          </p>
          
          {modelInfo && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm font-semibold text-blue-900 mb-2">Active Model:</p>
              <div className="text-sm text-blue-800 space-y-1">
                <p>Model Type: <span className="font-medium">{modelInfo.model_type}</span></p>
                {modelInfo.metrics && (
                  <p>Accuracy: <span className="font-medium">{(modelInfo.metrics.accuracy * 100).toFixed(2)}%</span></p>
                )}
                <p className="text-xs text-blue-600">
                  Trained on: {new Date(modelInfo.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          )}

          {!modelInfo && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                ⚠️ No trained model found. The system will use rule-based prediction. 
                Train a model first to use your custom ML model.
              </p>
            </div>
          )}
        </div>

        <div className="card">
          <div className="mb-6">
            <label htmlFor="test-text" className="block text-sm font-medium text-gray-700 mb-2">
              Enter Text to Test
            </label>
            <textarea
              id="test-text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="input-field h-48 resize-none"
              placeholder="Enter text here to test your model. For example:&#10;&#10;'I have been feeling very anxious lately and having trouble sleeping. I feel overwhelmed with work and personal responsibilities.'&#10;&#10;or&#10;&#10;'I feel great today! I had a good night's sleep and I'm excited about my upcoming projects.'"
              disabled={loading}
            />
            <p className="mt-2 text-sm text-gray-500">
              {text.length} characters
            </p>
          </div>

          <div className="flex gap-4">
            <button
              onClick={handleSubmit}
              disabled={loading || !text.trim()}
              className="btn-primary flex-1"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Testing...
                </span>
              ) : (
                'Test Model'
              )}
            </button>
            <button
              onClick={() => {
                setText('')
                setResult(null)
              }}
              disabled={loading}
              className="btn-secondary"
            >
              Clear
            </button>
          </div>
        </div>

        <div className="mt-6 card bg-gray-50">
          <h2 className="text-lg font-semibold mb-3">Example Test Cases</h2>
          <div className="space-y-3">
            <div className="p-3 bg-white rounded-lg border border-gray-200">
              <p className="text-sm font-medium text-gray-700 mb-1">High Risk Example:</p>
              <p className="text-sm text-gray-600 italic">
                "I've been feeling extremely depressed for weeks. I can't sleep, I've lost interest in everything, and I've been having thoughts about hurting myself. Nothing seems to help."
              </p>
            </div>
            <div className="p-3 bg-white rounded-lg border border-gray-200">
              <p className="text-sm font-medium text-gray-700 mb-1">Medium Risk Example:</p>
              <p className="text-sm text-gray-600 italic">
                "I've been feeling anxious and stressed lately. Work has been overwhelming and I'm having trouble concentrating. I feel tired all the time."
              </p>
            </div>
            <div className="p-3 bg-white rounded-lg border border-gray-200">
              <p className="text-sm font-medium text-gray-700 mb-1">Low Risk Example:</p>
              <p className="text-sm text-gray-600 italic">
                "I'm doing well overall. Sometimes I feel a bit stressed, but I have good coping mechanisms and a supportive network of friends and family."
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              const examples = [
                "I've been feeling extremely depressed for weeks. I can't sleep, I've lost interest in everything, and I've been having thoughts about hurting myself. Nothing seems to help.",
                "I've been feeling anxious and stressed lately. Work has been overwhelming and I'm having trouble concentrating. I feel tired all the time.",
                "I'm doing well overall. Sometimes I feel a bit stressed, but I have good coping mechanisms and a supportive network of friends and family."
              ]
              const randomExample = examples[Math.floor(Math.random() * examples.length)]
              setText(randomExample)
            }}
            className="mt-4 btn-secondary btn-sm"
          >
            Load Random Example
          </button>
        </div>

        <div className="mt-6 card bg-yellow-50 border-yellow-200">
          <p className="text-sm text-yellow-800">
            <strong>Note:</strong> This tool uses your trained model to predict mental health risk levels from text input. 
            The model analyzes the text and provides a risk assessment along with explanations of which features influenced the prediction.
          </p>
        </div>
      </div>
    </div>
  )
}

