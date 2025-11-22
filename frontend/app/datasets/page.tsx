'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Nav from '@/components/Nav'
import Link from 'next/link'
import toast from 'react-hot-toast'

export default function DatasetsPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [datasets, setDatasets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }

    fetchDatasets()
  }, [isAuthenticated, router])

  const fetchDatasets = async () => {
    try {
      const response = await api.get('/api/datasets/')
      setDatasets(response.data)
    } catch (error: any) {
      toast.error('Failed to load datasets')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this dataset?')) return

    try {
      await api.delete(`/api/datasets/${id}`)
      toast.success('Dataset deleted')
      fetchDatasets()
    } catch (error: any) {
      toast.error('Failed to delete dataset')
    }
  }

  if (!isAuthenticated) return null

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-display font-bold text-gray-900">Datasets</h1>
          <Link href="/datasets/upload" className="btn-primary">
            Upload Dataset
          </Link>
        </div>

        {loading ? (
          <div className="card text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-700 mx-auto"></div>
          </div>
        ) : datasets.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-600 mb-4">No datasets uploaded yet</p>
            <Link href="/datasets/upload" className="btn-primary">
              Upload Your First Dataset
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {datasets.map((dataset) => (
              <div key={dataset.id} className="card">
                <h3 className="text-lg font-semibold mb-2">{dataset.name}</h3>
                <p className="text-sm text-gray-600 mb-4">
                  {dataset.row_count} rows • {dataset.is_private ? 'Private' : 'Public'}
                </p>
                <div className="flex gap-2">
                  <Link
                    href={`/datasets/${dataset.id}`}
                    className="btn-secondary flex-1 text-center text-sm py-2"
                  >
                    View
                  </Link>
                  <button
                    onClick={() => handleDelete(dataset.id)}
                    className="px-4 py-2 text-danger hover:bg-red-50 rounded-xl text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

