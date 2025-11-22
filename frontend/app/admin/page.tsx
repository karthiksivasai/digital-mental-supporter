'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Nav from '@/components/Nav'
import toast from 'react-hot-toast'
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function AdminPage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuthStore()
  const [analytics, setAnalytics] = useState<any>(null)
  const [models, setModels] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated || !user?.is_admin) {
      router.push('/dashboard')
      return
    }

    fetchData()
  }, [isAuthenticated, user, router])

  const fetchData = async () => {
    try {
      const [analyticsRes, modelsRes] = await Promise.all([
        api.get('/api/admin/analytics'),
        api.get('/api/admin/models'),
      ])
      setAnalytics(analyticsRes.data)
      setModels(modelsRes.data)
    } catch (error: any) {
      toast.error('Failed to load admin data')
    } finally {
      setLoading(false)
    }
  }

  const activateModel = async (modelId: number) => {
    try {
      await api.post(`/api/admin/models/${modelId}/activate`)
      toast.success('Model activated')
      fetchData()
    } catch (error: any) {
      toast.error('Failed to activate model')
    }
  }

  if (!isAuthenticated || !user?.is_admin) return null

  const COLORS = ['#0f766e', '#06b6d4', '#16a34a', '#f59e0b']

  const labelData = analytics?.label_distribution
    ? Object.entries(analytics.label_distribution).map(([name, value]) => ({
        name,
        value,
      }))
    : []

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-display font-bold text-gray-900 mb-8">Admin Dashboard</h1>

        {loading ? (
          <div className="card text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-700 mx-auto"></div>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="card">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Total Uploads</h3>
                <p className="text-3xl font-bold text-primary-700">{analytics?.total_uploads || 0}</p>
              </div>
              <div className="card">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Total Trainings</h3>
                <p className="text-3xl font-bold text-accent-500">{analytics?.total_trainings || 0}</p>
              </div>
              <div className="card">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Total Predictions</h3>
                <p className="text-3xl font-bold text-success">{analytics?.total_predictions || 0}</p>
              </div>
              <div className="card">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Avg Score</h3>
                <p className="text-3xl font-bold text-warning">
                  {analytics?.average_score?.toFixed(1) || '0'}
                </p>
              </div>
            </div>

            {analytics?.model_drift_alert && (
              <div className="card bg-yellow-50 border-yellow-200 mb-6">
                <p className="text-yellow-800 font-semibold">
                  ⚠️ Model Drift Alert: Recent predictions show significant shift from training baseline
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Label Distribution</h2>
                {labelData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={labelData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {labelData.map((entry: any, index: number) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-gray-600 text-center py-12">No data available</p>
                )}
              </div>

              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Models</h2>
                <div className="space-y-3">
                  {models.length === 0 ? (
                    <p className="text-gray-600 text-center py-8">No models trained yet</p>
                  ) : (
                    models.map((model) => (
                      <div
                        key={model.id}
                        className="border border-gray-200 rounded-xl p-4"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h3 className="font-semibold">{model.version}</h3>
                            <p className="text-sm text-gray-600">{model.model_type}</p>
                          </div>
                          {model.is_active ? (
                            <span className="px-3 py-1 bg-success text-white rounded-full text-sm font-medium">
                              Active
                            </span>
                          ) : (
                            <button
                              onClick={() => activateModel(model.id)}
                              className="btn-secondary text-sm py-1 px-3"
                            >
                              Activate
                            </button>
                          )}
                        </div>
                        {model.metrics && (
                          <div className="text-sm text-gray-600">
                            Accuracy: {(model.metrics.accuracy * 100).toFixed(1)}% • F1:{' '}
                            {(model.metrics.f1 * 100).toFixed(1)}%
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

