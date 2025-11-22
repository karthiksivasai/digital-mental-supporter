'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Nav from '@/components/Nav'
import toast from 'react-hot-toast'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import ModelComparison from '@/components/ModelComparison'

export default function TrainingPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [datasets, setDatasets] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [selectedDataset, setSelectedDataset] = useState('')
  const [modelType, setModelType] = useState('logistic_regression')
  const [useSmote, setUseSmote] = useState(false)
  const [loading, setLoading] = useState(false)
  const [autoTrainingLoading, setAutoTrainingLoading] = useState(false)
  const [selectedAutoJob, setSelectedAutoJob] = useState<string | null>(null)
  const [autoTrainingResults, setAutoTrainingResults] = useState<any>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }

    fetchDatasets()
    fetchJobs()
    const interval = setInterval(fetchJobs, 5000) // Poll every 5 seconds
    return () => clearInterval(interval)
  }, [isAuthenticated, router])

  useEffect(() => {
    // Auto-select auto-training job when it appears
    const autoJob = jobs.find(job => job.model_type === 'auto_training' && (job.status === 'running' || job.status === 'completed'))
    if (autoJob && autoJob.job_id !== selectedAutoJob) {
      setSelectedAutoJob(autoJob.job_id)
      fetchAutoTrainingResults(autoJob.job_id)
    }
  }, [jobs, selectedAutoJob])

  const fetchDatasets = async () => {
    try {
      const response = await api.get('/api/datasets/')
      setDatasets(response.data)
    } catch (error) {
      // Ignore
    }
  }

  const fetchJobs = async () => {
    try {
      const response = await api.get('/api/training/jobs')
      setJobs(response.data || [])
      
      // Fetch auto-training results if there's a selected auto job
      if (selectedAutoJob) {
        fetchAutoTrainingResults(selectedAutoJob)
      }
    } catch (error: any) {
      console.error('Failed to fetch jobs:', error)
      setJobs([])
    }
  }

  const fetchAutoTrainingResults = async (jobId: string) => {
    try {
      const response = await api.get(`/api/training/auto/${jobId}/results`)
      setAutoTrainingResults(response.data)
    } catch (error: any) {
      console.error('Failed to fetch auto-training results:', error)
    }
  }

  const startTraining = async () => {
    if (!selectedDataset) {
      toast.error('Please select a dataset')
      return
    }

    // Check if there's already an active job
    const activeJob = jobs.find(job => 
      job.status === 'pending' || job.status === 'running'
    )
    if (activeJob) {
      toast.error('Another training job is already in progress. Please wait for it to complete or cancel it first.')
      return
    }

    setLoading(true)
    try {
      const response = await api.post('/api/training/start', {
        dataset_id: parseInt(selectedDataset),
        model_type: modelType,
        use_smote: useSmote,
      })
      toast.success('Training started!')
      fetchJobs()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start training')
    } finally {
      setLoading(false)
    }
  }

  const startAutoTraining = async () => {
    if (!selectedDataset) {
      toast.error('Please select a dataset')
      return
    }

    // Check if there's already an active job
    const activeJob = jobs.find(job => 
      job.status === 'pending' || job.status === 'running'
    )
    if (activeJob) {
      toast.error('Another training job is already in progress. Please wait for it to complete or cancel it first.')
      return
    }

    setAutoTrainingLoading(true)
    try {
      const response = await api.post('/api/training/auto', {
        dataset_id: parseInt(selectedDataset),
        use_smote: useSmote,
      })
      toast.success('Auto-training started! Training 5 models...')
      setSelectedAutoJob(response.data.job_id)
      fetchJobs()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start auto-training')
    } finally {
      setAutoTrainingLoading(false)
    }
  }

  const downloadMetricsReport = async () => {
    try {
      const response = await api.get('/api/training/metrics-report', {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'metrics_report.json')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('Metrics report downloaded')
    } catch (error: any) {
      toast.error('Failed to download metrics report. The report may not be available yet.')
    }
  }

  const pauseTraining = async (jobId: string) => {
    try {
      await api.post(`/api/training/${jobId}/pause`)
      toast.success('Training paused')
      fetchJobs()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to pause training')
    }
  }

  const cancelTraining = async (jobId: string) => {
    if (!confirm('Are you sure you want to cancel this training job?')) {
      return
    }
    try {
      await api.post(`/api/training/${jobId}/cancel`)
      toast.success('Training cancelled')
      fetchJobs()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to cancel training')
    }
  }

  const deleteJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this training job? This action cannot be undone.')) {
      return
    }
    try {
      await api.delete(`/api/training/${jobId}`)
      toast.success('Training job deleted')
      fetchJobs()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete job')
    }
  }

  const formatTime = (seconds: number): string => {
    if (!seconds || seconds < 0) return '0s'
    if (seconds < 60) return `${Math.round(seconds)}s`
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  const estimateTrainingTime = (dataset: any, modelType: string, useSmote: boolean): string => {
    if (!dataset || !dataset.row_count) return 'Unknown'
    
    const rowCount = dataset.row_count
    let baseTimePer1000Rows = 10 // seconds per 1000 rows for logistic regression
    
    if (modelType === 'random_forest') {
      baseTimePer1000Rows = 30 // Random Forest is slower
    }
    
    if (useSmote) {
      baseTimePer1000Rows *= 1.5 // SMOTE adds overhead
    }
    
    const estimatedSeconds = (rowCount / 1000) * baseTimePer1000Rows
    
    if (estimatedSeconds < 30) return '< 30 seconds'
    if (estimatedSeconds < 120) return '1-2 minutes'
    if (estimatedSeconds < 300) return '2-5 minutes'
    if (estimatedSeconds < 600) return '5-10 minutes'
    return '10+ minutes'
  }

  if (!isAuthenticated) return null

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-display font-bold text-gray-900 mb-8">Training</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Start Training</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dataset
                  </label>
                  <select
                    value={selectedDataset}
                    onChange={(e) => setSelectedDataset(e.target.value)}
                    className="input-field"
                  >
                    <option value="">Select dataset...</option>
                    {datasets.map((ds) => (
                      <option key={ds.id} value={ds.id}>
                        {ds.name} ({ds.row_count} rows)
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model Type
                  </label>
                  <select
                    value={modelType}
                    onChange={(e) => setModelType(e.target.value)}
                    className="input-field"
                  >
                    <option value="logistic_regression">Logistic Regression</option>
                    <option value="random_forest">Random Forest</option>
                  </select>
                </div>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={useSmote}
                    onChange={(e) => setUseSmote(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Use SMOTE (for imbalanced data)</span>
                </label>

                {selectedDataset && (
                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Estimated Time:</strong>{' '}
                      {estimateTrainingTime(
                        datasets.find(ds => ds.id === parseInt(selectedDataset)),
                        modelType,
                        useSmote
                      )}
                    </p>
                    <p className="text-xs text-blue-600 mt-1">
                      * Estimate based on dataset size and model type
                    </p>
                  </div>
                )}

                <button
                  onClick={startTraining}
                  disabled={loading || autoTrainingLoading || !selectedDataset || jobs.some(job => job.status === 'pending' || job.status === 'running')}
                  className="btn-primary w-full mb-3"
                >
                  {loading ? 'Starting...' : jobs.some(job => job.status === 'pending' || job.status === 'running') ? 'Training in Progress' : 'Start Training'}
                </button>

                <div className="border-t border-gray-200 pt-4 mt-4">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">🔥 Auto Train Models</h3>
                  <p className="text-xs text-gray-600 mb-3">
                    Automatically train and compare 5 models (Logistic Regression, Random Forest, SVM, XGBoost, ANN) and select the best one.
                  </p>
                  <button
                    onClick={startAutoTraining}
                    disabled={autoTrainingLoading || loading || !selectedDataset || jobs.some(job => job.status === 'pending' || job.status === 'running')}
                    className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {autoTrainingLoading ? 'Starting Auto-Training...' : '🚀 Auto Train Models'}
                  </button>
                </div>

                {jobs.some(job => job.status === 'pending' || job.status === 'running') && (
                  <p className="text-sm text-yellow-600 text-center mt-3">
                    ⚠️ Another training job is in progress
                  </p>
                )}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Training Jobs</h2>
              <div className="space-y-4">
                {jobs.length === 0 ? (
                  <p className="text-gray-600 text-center py-8">No training jobs yet</p>
                ) : (
                  jobs.map((job) => (
                    <div key={job.job_id} className="border border-gray-200 rounded-xl p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <h3 className="font-semibold">
                            Job {job.job_id.substring(0, 8)}
                            {job.model_type === 'auto_training' && (
                              <span className="ml-2 text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">AUTO</span>
                            )}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {job.model_type === 'auto_training' ? 'Auto Training (5 models)' : job.model_type} • {new Date(job.created_at).toLocaleString()}
                          </p>
                          {job.model_type === 'auto_training' && job.status === 'running' && (
                            <p className="text-xs text-blue-600 mt-1">
                              Training: Logistic Regression → Random Forest → SVM → XGBoost → ANN
                            </p>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-3 py-1 rounded-full text-sm font-medium ${
                              job.status === 'completed'
                                ? 'bg-green-500 text-white'
                                : job.status === 'failed' || job.status === 'cancelled'
                                ? 'bg-red-500 text-white'
                                : job.status === 'paused'
                                ? 'bg-yellow-500 text-white'
                                : 'bg-blue-500 text-white'
                            }`}
                          >
                            {job.status}
                          </span>
                          <div className="flex gap-1">
                            {(job.status === 'pending' || job.status === 'running') && (
                              <>
                                <button
                                  onClick={() => pauseTraining(job.job_id)}
                                  className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200"
                                  title="Pause training"
                                >
                                  ⏸️
                                </button>
                                <button
                                  onClick={() => cancelTraining(job.job_id)}
                                  className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
                                  title="Cancel training"
                                >
                                  ❌
                                </button>
                              </>
                            )}
                            {job.status === 'paused' && (
                              <button
                                onClick={() => cancelTraining(job.job_id)}
                                className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
                                title="Cancel training"
                              >
                                ⏹️ Cancel
                              </button>
                            )}
                            <button
                              onClick={() => deleteJob(job.job_id)}
                              className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded hover:bg-gray-200"
                              title="Delete job"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      </div>
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full transition-all"
                            style={{ width: `${job.progress * 100}%` }}
                          />
                        </div>
                        <div className="flex justify-between items-center mt-1">
                          <p className="text-xs text-gray-500">
                            {Math.round(job.progress * 100)}% complete
                          </p>
                          {job.status === 'running' && job.elapsed_seconds && (
                            <div className="text-xs text-gray-500">
                              {formatTime(job.elapsed_seconds)}
                              {job.estimated_remaining_seconds && job.estimated_remaining_seconds > 0 && (
                                <span className="ml-2 text-gray-400">
                                  • ~{formatTime(job.estimated_remaining_seconds)} remaining
                                </span>
                              )}
                            </div>
                          )}
                          {job.status === 'completed' && job.completed_at && job.started_at && (
                            <p className="text-xs text-green-600">
                              Completed in {formatTime(job.elapsed_seconds || 0)}
                            </p>
                          )}
                        </div>
                      </div>
                      {job.metrics && job.status === 'completed' && (
                        <div className="mt-4">
                          <div className="grid grid-cols-4 gap-2 text-sm mb-4">
                            <div>
                              <span className="text-gray-600">Accuracy:</span>
                              <span className="font-semibold ml-1">
                                {job.metrics.accuracy ? (job.metrics.accuracy * 100).toFixed(1) : 'N/A'}%
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600">Precision:</span>
                              <span className="font-semibold ml-1">
                                {job.metrics.precision ? (job.metrics.precision * 100).toFixed(1) : 'N/A'}%
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600">Recall:</span>
                              <span className="font-semibold ml-1">
                                {job.metrics.recall ? (job.metrics.recall * 100).toFixed(1) : 'N/A'}%
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600">F1:</span>
                              <span className="font-semibold ml-1">
                                {job.metrics.f1 ? (job.metrics.f1 * 100).toFixed(1) : 'N/A'}%
                              </span>
                            </div>
                          </div>

                          {/* Auto-training results */}
                          {job.model_type === 'auto_training' && job.status === 'completed' && (
                            <ModelComparison />
                          )}
                        </div>
                      )}
                      {job.error_message && (
                        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                          <p className="text-sm text-red-800">
                            <strong>Error:</strong> {job.error_message}
                          </p>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

