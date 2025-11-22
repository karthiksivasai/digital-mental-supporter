'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Nav from '@/components/Nav'
import toast from 'react-hot-toast'

export default function DatasetDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { isAuthenticated } = useAuthStore()
  const [dataset, setDataset] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }

    fetchDataset()
  }, [isAuthenticated, router, params.id])

  const fetchDataset = async () => {
    try {
      const response = await api.get(`/api/datasets/${params.id}`)
      setDataset(response.data)
    } catch (error: any) {
      toast.error('Failed to load dataset')
      router.push('/datasets')
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated || loading) return null

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {dataset && (
          <div className="card">
            <h1 className="text-3xl font-display font-bold text-gray-900 mb-6">
              {dataset.name}
            </h1>
            <div className="space-y-4">
              <div>
                <span className="text-sm font-medium text-gray-600">Filename:</span>
                <span className="ml-2 text-gray-900">{dataset.filename}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Rows:</span>
                <span className="ml-2 text-gray-900">{dataset.row_count}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Text Column:</span>
                <span className="ml-2 text-gray-900">{dataset.text_column}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Label Column:</span>
                <span className="ml-2 text-gray-900">{dataset.label_column}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Privacy:</span>
                <span className="ml-2 text-gray-900">
                  {dataset.is_private ? 'Private' : 'Public'}
                </span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Anonymized:</span>
                <span className="ml-2 text-gray-900">
                  {dataset.is_anonymous ? 'Yes' : 'No'}
                </span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Created:</span>
                <span className="ml-2 text-gray-900">
                  {new Date(dataset.created_at).toLocaleString()}
                </span>
              </div>
            </div>
            <div className="mt-6">
              <button
                onClick={() => router.push('/datasets')}
                className="btn-secondary"
              >
                Back to Datasets
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

