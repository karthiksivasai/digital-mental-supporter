'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Nav from '@/components/Nav'
import toast from 'react-hot-toast'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface FeatureImportance {
  feature: string
  importance: number
}

interface FeatureContribution {
  feature: string
  shap_value: number
  contribution: number
}

interface GlobalExplanation {
  feature_importance: FeatureImportance[]
  summary_plot: string
  bar_plot: string
  model_type: string
  n_samples: number
}

interface LocalExplanation {
  prediction: number
  prediction_proba: {
    class_0: number
    class_1: number
  }
  feature_contributions: FeatureContribution[]
  force_plot: string
  waterfall_plot: string
  lime_explanation: any
  base_value: number
  input_text: string
}

export default function ExplainPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [loading, setLoading] = useState(false)
  const [globalLoading, setGlobalLoading] = useState(false)
  const [localLoading, setLocalLoading] = useState(false)
  const [globalExplanation, setGlobalExplanation] = useState<GlobalExplanation | null>(null)
  const [localExplanation, setLocalExplanation] = useState<LocalExplanation | null>(null)
  const [inputText, setInputText] = useState('')
  const [modelAvailable, setModelAvailable] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }
    checkModelAvailability()
  }, [isAuthenticated, router])

  const checkModelAvailability = async () => {
    try {
      const response = await api.get('/api/explain/health')
      setModelAvailable(response.data.model_exists)
    } catch (error) {
      setModelAvailable(false)
    }
  }

  const explainGlobal = async () => {
    try {
      setGlobalLoading(true)
      setGlobalExplanation(null)
      
      const response = await api.get('/api/explain/global')
      setGlobalExplanation(response.data)
      toast.success('Global explanation generated successfully')
    } catch (error: any) {
      console.error('Failed to generate global explanation:', error)
      toast.error(error.response?.data?.detail || 'Failed to generate global explanation')
    } finally {
      setGlobalLoading(false)
    }
  }

  const explainLocal = async () => {
    if (!inputText.trim()) {
      toast.error('Please enter some text to explain')
      return
    }

    try {
      setLocalLoading(true)
      setLocalExplanation(null)
      
      const response = await api.post('/api/explain/local', {
        text: inputText
      })
      setLocalExplanation(response.data)
      toast.success('Local explanation generated successfully')
    } catch (error: any) {
      console.error('Failed to generate local explanation:', error)
      toast.error(error.response?.data?.detail || 'Failed to generate local explanation')
    } finally {
      setLocalLoading(false)
    }
  }

  if (!isAuthenticated) return null

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-display font-bold text-gray-900 mb-2">Model Explainability</h1>
        <p className="text-gray-600 mb-8">
          Understand how the model makes predictions using SHAP and LIME explanations
        </p>

        {!modelAvailable && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-yellow-800">
              ⚠️ No trained model found. Please train a model first before using explainability features.
            </p>
          </div>
        )}

        {/* Global Explanation Section */}
        <div className="card mb-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-semibold">Global Model Explanation</h2>
              <p className="text-sm text-gray-600 mt-1">
                Understand overall feature importance across all predictions
              </p>
            </div>
            <button
              onClick={explainGlobal}
              disabled={globalLoading || !modelAvailable}
              className="btn-primary"
            >
              {globalLoading ? 'Generating...' : '🔍 Explain Global Model Behavior'}
            </button>
          </div>

          {globalLoading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-700"></div>
              <p className="mt-2 text-gray-600">Generating global explanation...</p>
              <p className="mt-1 text-sm text-gray-500">This may take 10-30 seconds depending on your model type</p>
              <div className="mt-4 max-w-md mx-auto">
                <div className="bg-gray-200 rounded-full h-2">
                  <div className="bg-primary-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                </div>
              </div>
            </div>
          )}

          {globalExplanation && (
            <div className="space-y-6">
              {/* Feature Importance Table */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Top Feature Importance</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Rank</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Feature</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Importance</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {globalExplanation.feature_importance.slice(0, 20).map((feature, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3 whitespace-nowrap text-sm font-medium">{idx + 1}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">{feature.feature}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                            {feature.importance.toFixed(6)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Feature Importance Chart */}
              {globalExplanation.feature_importance.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Feature Importance Chart</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={globalExplanation.feature_importance.slice(0, 15).reverse()}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="feature" type="category" width={200} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="importance" fill="#3b82f6" name="SHAP Importance" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* SHAP Plots */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {globalExplanation.summary_plot && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">SHAP Summary Plot</h3>
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <img
                        src={globalExplanation.summary_plot}
                        alt="SHAP Summary Plot"
                        className="w-full h-auto"
                      />
                    </div>
                  </div>
                )}

                {globalExplanation.bar_plot && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">SHAP Bar Plot</h3>
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <img
                        src={globalExplanation.bar_plot}
                        alt="SHAP Bar Plot"
                        className="w-full h-auto"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="text-sm text-gray-600">
                <p><strong>Model Type:</strong> {globalExplanation.model_type}</p>
                <p><strong>Background Samples:</strong> {globalExplanation.n_samples}</p>
              </div>
            </div>
          )}
        </div>

        {/* Local Explanation Section */}
        <div className="card">
          <div className="mb-4">
            <h2 className="text-xl font-semibold mb-2">Individual Prediction Explanation</h2>
            <p className="text-sm text-gray-600">
              Understand how the model makes predictions for specific input text
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter text to explain:
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="e.g., I feel sad and anxious about my future..."
              className="input-field h-32 resize-none"
            />
            <button
              onClick={explainLocal}
              disabled={localLoading || !modelAvailable || !inputText.trim()}
              className="btn-primary mt-3"
            >
              {localLoading ? 'Generating...' : '🔍 Explain This Prediction'}
            </button>
          </div>

          {localLoading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-700"></div>
              <p className="mt-2 text-gray-600">Generating local explanation...</p>
            </div>
          )}

          {localExplanation && (
            <div className="space-y-6">
              {/* Prediction Summary */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2">Prediction Summary</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Predicted Class</p>
                    <p className="text-lg font-semibold">
                      {localExplanation.prediction === 1 ? 'High Risk' : 'Low Risk'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Confidence</p>
                    <p className="text-lg font-semibold">
                      {(localExplanation.prediction_proba.class_1 * 100).toFixed(2)}%
                    </p>
                  </div>
                </div>
                <div className="mt-3">
                  <p className="text-sm text-gray-600">Input Text:</p>
                  <p className="text-sm font-medium mt-1">{localExplanation.input_text}</p>
                </div>
              </div>

              {/* Feature Contributions Table */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Feature Contributions</h3>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Feature</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">SHAP Value</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Impact</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {localExplanation.feature_contributions.map((contrib, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                            {contrib.feature}
                          </td>
                          <td className={`px-4 py-3 whitespace-nowrap text-sm font-medium ${
                            contrib.shap_value > 0 ? 'text-red-600' : 'text-blue-600'
                          }`}>
                            {contrib.shap_value > 0 ? '+' : ''}{contrib.shap_value.toFixed(6)}
                          </td>
                          <td className="px-4 py-3 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              contrib.shap_value > 0 
                                ? 'bg-red-100 text-red-800' 
                                : 'bg-blue-100 text-blue-800'
                            }`}>
                              {contrib.shap_value > 0 ? 'Increases Risk' : 'Decreases Risk'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Feature Contributions Chart */}
              {localExplanation.feature_contributions.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Feature Contributions Chart</h3>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={localExplanation.feature_contributions.slice(0, 15).reverse()}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="feature" type="category" width={200} tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Legend />
                      <Bar 
                        dataKey="shap_value" 
                        name="SHAP Value"
                        fill={(entry: any) => entry.shap_value > 0 ? '#ef4444' : '#3b82f6'}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* SHAP Plots */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {localExplanation.force_plot && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">SHAP Force Plot</h3>
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <img
                        src={localExplanation.force_plot}
                        alt="SHAP Force Plot"
                        className="w-full h-auto"
                      />
                    </div>
                  </div>
                )}

                {localExplanation.waterfall_plot && (
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Waterfall Plot</h3>
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <img
                        src={localExplanation.waterfall_plot}
                        alt="Waterfall Plot"
                        className="w-full h-auto"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* LIME Explanation */}
              {localExplanation.lime_explanation && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">LIME Explanation</h3>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                      {JSON.stringify(localExplanation.lime_explanation, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              <div className="text-sm text-gray-600">
                <p><strong>Base Value:</strong> {localExplanation.base_value.toFixed(6)}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

