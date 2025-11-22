'use client'

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import toast from 'react-hot-toast'
import jsPDF from 'jspdf'

interface ModelMetrics {
  model: string
  accuracy: number
  precision: number
  recall: number
  f1: number
  training_time: number
  status?: string
}

interface MetricsReport {
  timestamp?: string
  best_model?: string
  models_ranked?: ModelMetrics[]
  all_models_metrics?: {
    [key: string]: {
      metrics: {
        accuracy: number
        precision: number
        recall: number
        f1: number
      }
      training_time: number
      status: string
    }
  }
}

export default function ModelComparison() {
  const [report, setReport] = useState<MetricsReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showJsonModal, setShowJsonModal] = useState(false)
  const [jsonData, setJsonData] = useState<string>('')

  useEffect(() => {
    fetchMetricsReport()
  }, [])

  const fetchMetricsReport = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/api/training/metrics-report', {
        responseType: 'blob'
      })
      
      // Convert blob to JSON
      const text = await response.data.text()
      const data = JSON.parse(text) as MetricsReport
      
      // Transform data if needed - ensure models_ranked has all required fields
      if (data.all_models_metrics && (!data.models_ranked || data.models_ranked.length === 0)) {
        data.models_ranked = Object.entries(data.all_models_metrics)
          .filter(([_, result]) => result.status === 'success')
          .map(([name, result]) => ({
            model: name,
            accuracy: result.metrics.accuracy,
            precision: result.metrics.precision,
            recall: result.metrics.recall,
            f1: result.metrics.f1,
            training_time: result.training_time,
            status: result.status
          }))
          .sort((a, b) => (b.f1 * 100 + b.accuracy * 100) - (a.f1 * 100 + a.accuracy * 100))
      }
      
      // Ensure models_ranked has precision and recall if missing
      if (data.models_ranked && data.all_models_metrics) {
        data.models_ranked = data.models_ranked.map((model: any) => {
          if (!model.precision || !model.recall) {
            const modelData = data.all_models_metrics?.[model.model]
            if (modelData) {
              return {
                ...model,
                precision: model.precision ?? modelData.metrics.precision,
                recall: model.recall ?? modelData.metrics.recall
              }
            }
          }
          return model
        })
      }
      
      setReport(data)
      setJsonData(JSON.stringify(data, null, 2))
    } catch (err: any) {
      console.error('Failed to fetch metrics report:', err)
      if (err.response?.status === 404) {
        setError('Metrics report not available yet. Please complete an auto-training job first.')
      } else {
        setError('Failed to load metrics report')
      }
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (seconds: number): string => {
    if (!seconds || seconds < 0) return '0s'
    if (seconds < 60) return `${seconds.toFixed(2)}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}h ${minutes}m`
  }

  const formatModelName = (name: string): string => {
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  const getMetricColor = (value: number): string => {
    const percentage = value * 100
    if (percentage >= 95) return 'text-green-600 font-semibold'
    if (percentage >= 80) return 'text-yellow-600 font-semibold'
    return 'text-red-600 font-semibold'
  }

  const getMetricBgColor = (value: number): string => {
    const percentage = value * 100
    if (percentage >= 95) return 'bg-green-50'
    if (percentage >= 80) return 'bg-yellow-50'
    return 'bg-red-50'
  }

  const downloadJson = async () => {
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
      toast.error('Failed to download metrics report')
    }
  }

  const downloadPdf = async () => {
    try {
      // Dynamic import for html2canvas
      const html2canvas = (await import('html2canvas')).default
      
      const element = document.getElementById('model-comparison-content')
      if (!element) {
        toast.error('Content not found')
        return
      }

      toast.loading('Generating PDF...', { id: 'pdf-loading' })
      
      const canvas = await html2canvas(element, {
        scale: 2,
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff'
      })

      const imgData = canvas.toDataURL('image/png')
      const pdf = new jsPDF('landscape', 'mm', 'a4')
      
      const pdfWidth = pdf.internal.pageSize.getWidth()
      const pdfHeight = pdf.internal.pageSize.getHeight()
      const imgWidth = canvas.width
      const imgHeight = canvas.height
      const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight)
      const imgX = (pdfWidth - imgWidth * ratio) / 2
      const imgY = 0

      pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio)
      pdf.save('model_comparison_report.pdf')
      
      toast.success('PDF downloaded successfully', { id: 'pdf-loading' })
    } catch (error: any) {
      console.error('PDF generation error:', error)
      toast.error('Failed to generate PDF. Please try again.', { id: 'pdf-loading' })
    }
  }

  const viewJson = () => {
    setShowJsonModal(true)
  }

  if (loading) {
    return (
      <div className="mt-4 border-t border-gray-200 pt-4">
        <div className="flex justify-between items-center mb-3">
          <h4 className="font-semibold text-gray-800">Model Comparison</h4>
        </div>
        <div className="space-y-4">
          {/* Skeleton Loading */}
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="space-y-2">
              <div className="h-12 bg-gray-200 rounded"></div>
              <div className="h-12 bg-gray-200 rounded"></div>
              <div className="h-12 bg-gray-200 rounded"></div>
              <div className="h-12 bg-gray-200 rounded"></div>
              <div className="h-12 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mt-4 border-t border-gray-200 pt-4">
        <div className="flex justify-between items-center mb-3">
          <h4 className="font-semibold text-gray-800">Model Comparison</h4>
        </div>
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">{error}</p>
        </div>
      </div>
    )
  }

  if (!report || !report.models_ranked || report.models_ranked.length === 0) {
    return (
      <div className="mt-4 border-t border-gray-200 pt-4">
        <div className="flex justify-between items-center mb-3">
          <h4 className="font-semibold text-gray-800">Model Comparison</h4>
        </div>
        <p className="text-sm text-gray-500">No model comparison data available</p>
      </div>
    )
  }

  const modelsData = report.models_ranked.filter(m => m.status !== 'failed')
  const bestModel = report.best_model || modelsData[0]?.model

  // Prepare data for charts
  const barChartData = modelsData.map(model => ({
    name: formatModelName(model.model),
    Accuracy: (model.accuracy * 100).toFixed(1),
    'F1 Score': (model.f1 * 100).toFixed(1)
  }))

  const trainingTimeData = modelsData.map(model => ({
    name: formatModelName(model.model),
    'Training Time (s)': model.training_time.toFixed(2)
  }))

  return (
    <>
      <div className="mt-4 border-t border-gray-200 pt-4" id="model-comparison-content">
        <div className="flex justify-between items-center mb-4">
          <h4 className="font-semibold text-gray-800 text-lg">Model Comparison</h4>
          <div className="flex gap-2">
            <button
              onClick={viewJson}
              className="text-xs bg-gray-100 text-gray-800 px-3 py-1.5 rounded hover:bg-gray-200 transition-colors"
            >
              📄 View JSON
            </button>
            <button
              onClick={downloadPdf}
              className="text-xs bg-red-100 text-red-800 px-3 py-1.5 rounded hover:bg-red-200 transition-colors"
            >
              📥 Download PDF Report
            </button>
            <button
              onClick={downloadJson}
              className="text-xs bg-blue-100 text-blue-800 px-3 py-1.5 rounded hover:bg-blue-200 transition-colors"
            >
              📥 Download Report (JSON)
            </button>
          </div>
        </div>

        {/* Comparison Table */}
        <div className="overflow-x-auto mb-6">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Rank</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Model Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Accuracy</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Precision</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Recall</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">F1 Score</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Training Time</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {modelsData.map((model, idx) => {
                const isBest = model.model === bestModel
                return (
                  <tr
                    key={idx}
                    className={`${isBest ? 'bg-gradient-to-r from-yellow-50 to-amber-50 border-l-4 border-yellow-500' : 'hover:bg-gray-50'} transition-colors`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="font-semibold">{idx + 1}</span>
                        {isBest && (
                          <span className="ml-2 text-yellow-600" title="Best Model">
                            ⭐
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className={`font-medium ${isBest ? 'text-yellow-800' : 'text-gray-900'}`}>
                          {formatModelName(model.model)}
                        </span>
                        {isBest && (
                          <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-200 text-yellow-800 rounded-full font-semibold">
                            BEST
                          </span>
                        )}
                      </div>
                    </td>
                    <td className={`px-4 py-3 whitespace-nowrap ${getMetricColor(model.accuracy)}`}>
                      {(model.accuracy * 100).toFixed(2)}%
                    </td>
                    <td className={`px-4 py-3 whitespace-nowrap ${getMetricColor(model.precision)}`}>
                      {(model.precision * 100).toFixed(2)}%
                    </td>
                    <td className={`px-4 py-3 whitespace-nowrap ${getMetricColor(model.recall)}`}>
                      {(model.recall * 100).toFixed(2)}%
                    </td>
                    <td className={`px-4 py-3 whitespace-nowrap ${getMetricColor(model.f1)}`}>
                      {(model.f1 * 100).toFixed(2)}%
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-gray-600">
                      {formatTime(model.training_time)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        model.status === 'success' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {model.status || 'success'}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Accuracy Bar Chart */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h5 className="text-sm font-semibold text-gray-700 mb-3">Accuracy Comparison</h5>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={barChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 10 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  tick={{ fontSize: 10 }}
                  domain={[0, 100]}
                  label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value: any) => `${value}%`}
                  contentStyle={{ fontSize: '12px' }}
                />
                <Legend />
                <Bar dataKey="Accuracy" fill="#3b82f6" name="Accuracy (%)" />
                <Bar dataKey="F1 Score" fill="#10b981" name="F1 Score (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Comparison Chart for Precision, Recall, F1 */}
          <div className="bg-white p-4 rounded-lg border border-gray-200">
            <h5 className="text-sm font-semibold text-gray-700 mb-3">Precision, Recall & F1 Score Comparison</h5>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={modelsData.map(model => ({
                name: formatModelName(model.model).substring(0, 8),
                Precision: (model.precision * 100).toFixed(1),
                Recall: (model.recall * 100).toFixed(1),
                'F1 Score': (model.f1 * 100).toFixed(1)
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 10 }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  tick={{ fontSize: 10 }}
                  domain={[0, 100]}
                  label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip 
                  formatter={(value: any) => `${value}%`}
                  contentStyle={{ fontSize: '12px' }}
                />
                <Legend />
                <Bar dataKey="Precision" fill="#3b82f6" name="Precision (%)" />
                <Bar dataKey="Recall" fill="#10b981" name="Recall (%)" />
                <Bar dataKey="F1 Score" fill="#f59e0b" name="F1 Score (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Training Time Chart */}
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h5 className="text-sm font-semibold text-gray-700 mb-3">Training Time Comparison</h5>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={trainingTimeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                tick={{ fontSize: 10 }}
                label={{ value: 'Time (seconds)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                formatter={(value: any) => `${value}s`}
                contentStyle={{ fontSize: '12px' }}
              />
              <Legend />
              <Bar dataKey="Training Time (s)" fill="#8b5cf6" name="Training Time (seconds)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* JSON Modal */}
      {showJsonModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
            <div className="flex justify-between items-center p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Metrics Report JSON</h3>
              <button
                onClick={() => setShowJsonModal(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            <div className="p-4 overflow-auto flex-1">
              <pre className="bg-gray-50 p-4 rounded-lg text-xs overflow-x-auto">
                <code>{jsonData}</code>
              </pre>
            </div>
            <div className="flex justify-end gap-2 p-4 border-t border-gray-200">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(jsonData)
                  toast.success('JSON copied to clipboard')
                }}
                className="px-4 py-2 bg-gray-100 text-gray-800 rounded hover:bg-gray-200 transition-colors"
              >
                Copy to Clipboard
              </button>
              <button
                onClick={() => setShowJsonModal(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

