'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { api } from '@/lib/api'
import Nav from '@/components/Nav'
import toast from 'react-hot-toast'

export default function UploadDatasetPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState('')
  const [textColumn, setTextColumn] = useState('')
  const [labelColumn, setLabelColumn] = useState('')
  const [isPrivate, setIsPrivate] = useState(true)
  const [isAnonymous, setIsAnonymous] = useState(false)
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<any>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setName(selectedFile.name.replace('.csv', ''))
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      toast.error('Please select a file')
      return
    }

    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('name', name)
      if (textColumn) formData.append('text_column', textColumn)
      if (labelColumn) formData.append('label_column', labelColumn)
      formData.append('is_private', String(isPrivate))
      formData.append('is_anonymous', String(isAnonymous))

      const response = await api.post('/api/datasets/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      setPreview(response.data)
      toast.success('Dataset uploaded successfully!')
      setTimeout(() => router.push('/datasets'), 2000)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    router.push('/auth/login')
    return null
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Nav />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-display font-bold text-gray-900 mb-8">Upload Dataset</h1>

        <form onSubmit={handleUpload} className="card space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              CSV File
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="input-field"
              required
            />
            <p className="text-sm text-gray-500 mt-1">
              Upload a CSV file with text and label columns
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dataset Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-field"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Text Column (auto-detected if empty)
              </label>
              <input
                type="text"
                value={textColumn}
                onChange={(e) => setTextColumn(e.target.value)}
                className="input-field"
                placeholder="Auto-detect"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Label Column (auto-detected if empty)
              </label>
              <input
                type="text"
                value={labelColumn}
                onChange={(e) => setLabelColumn(e.target.value)}
                className="input-field"
                placeholder="Auto-detect"
              />
            </div>
          </div>

          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={isPrivate}
                onChange={(e) => setIsPrivate(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Keep dataset private</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={isAnonymous}
                onChange={(e) => setIsAnonymous(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Anonymize PII (remove name/email columns)</span>
            </label>
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? 'Uploading...' : 'Upload Dataset'}
          </button>
        </form>

        {preview && (
          <div className="card mt-6">
            <h2 className="text-xl font-semibold mb-4">Preview</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {preview.preview && preview.preview[0] && Object.keys(preview.preview[0]).map((key) => (
                      <th key={key} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {preview.preview?.slice(0, 10).map((row: any, idx: number) => (
                    <tr key={idx}>
                      {Object.values(row).map((val: any, i: number) => (
                        <td key={i} className="px-4 py-2 text-sm text-gray-900">
                          {String(val).substring(0, 50)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

