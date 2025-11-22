'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Nav from '@/components/Nav'
import Link from 'next/link'
import toast from 'react-hot-toast'

export default function DashboardPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [stats, setStats] = useState({
    datasets: 0,
    trainings: 0,
    predictions: 0,
  })

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }

    // Fetch stats
    Promise.all([
      api.get('/api/datasets/').catch(() => ({ data: [] })),
      api.get('/api/training/jobs').catch(() => ({ data: [] })),
      api.get('/api/predictions/history').catch(() => ({ data: [] })),
    ]).then(([datasets, trainings, predictions]) => {
      setStats({
        datasets: datasets.data.length,
        trainings: trainings.data.length,
        predictions: predictions.data.length,
      })
    })
  }, [isAuthenticated, router])

  if (!isAuthenticated) return null

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-display font-bold text-gray-900 mb-8">Dashboard</h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Datasets</h3>
            <p className="text-3xl font-bold text-primary-700">{stats.datasets}</p>
            <Link href="/datasets" className="text-sm text-primary-600 hover:underline mt-2 inline-block">
              View all →
            </Link>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Training Jobs</h3>
            <p className="text-3xl font-bold text-accent-500">{stats.trainings}</p>
            <Link href="/training" className="text-sm text-accent-600 hover:underline mt-2 inline-block">
              View all →
            </Link>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Predictions</h3>
            <p className="text-3xl font-bold text-success">{stats.predictions}</p>
            <Link href="/questionnaire" className="text-sm text-success hover:underline mt-2 inline-block">
              New assessment →
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <Link href="/datasets/upload" className="btn-primary w-full block text-center">
                Upload Dataset
              </Link>
              <Link href="/questionnaire" className="btn-secondary w-full block text-center">
                Start Assessment
              </Link>
              <Link href="/training" className="btn-secondary w-full block text-center">
                Train Model
              </Link>
            </div>
          </div>

          <div className="card">
            <h2 className="text-xl font-semibold mb-4">Getting Started</h2>
            <div className="space-y-3 text-sm text-gray-600">
              <p>1. Upload a CSV dataset with text and label columns</p>
              <p>2. Train a model using your dataset</p>
              <p>3. Use the assessment tool to get predictions</p>
              <p>4. View results and explanations</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

