'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import jsPDF from 'jspdf'

interface ResultPageProps {
  result: {
    score: number
    label: string
    explanation: Array<{ feature: string; weight: number }>
    suggestions: string[]
    is_urgent: boolean
    emergency_contacts?: Array<{ name: string; phone: string; text: string; url: string }>
  }
}

export default function ResultPage({ result }: ResultPageProps) {
  const router = useRouter()
  const [showEmergency, setShowEmergency] = useState(result.is_urgent)

  const downloadPDF = () => {
    const doc = new jsPDF()
    doc.setFontSize(20)
    doc.text('Mental Health Assessment Results', 20, 20)
    doc.setFontSize(12)
    doc.text(`Score: ${result.score}/100`, 20, 40)
    doc.text(`Risk Level: ${result.label}`, 20, 50)
    doc.text('Suggestions:', 20, 70)
    result.suggestions.forEach((suggestion, index) => {
      doc.text(`• ${suggestion}`, 20, 80 + index * 10)
    })
    doc.save('assessment-results.pdf')
  }

  const getScoreColor = () => {
    if (result.label === 'High') return 'text-danger'
    if (result.label === 'Moderate') return 'text-warning'
    return 'text-success'
  }

  const getGaugeRotation = () => {
    return (result.score / 100) * 180 - 90
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {showEmergency && result.emergency_contacts && (
          <div className="card bg-red-50 border-2 border-danger mb-6">
            <h2 className="text-2xl font-bold text-danger mb-4">Immediate Support Available</h2>
            <div className="space-y-3">
              {result.emergency_contacts.map((contact, idx) => (
                <div key={idx} className="bg-white p-4 rounded-lg">
                  <h3 className="font-semibold text-lg">{contact.name}</h3>
                  <p className="text-gray-700">Phone: {contact.phone}</p>
                  {contact.text && <p className="text-gray-700">{contact.text}</p>}
                  {contact.url && (
                    <a
                      href={contact.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary-700 hover:underline"
                    >
                      Visit website →
                    </a>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={() => setShowEmergency(false)}
              className="mt-4 text-sm text-gray-600 hover:text-gray-800"
            >
              Close
            </button>
          </div>
        )}

        <div className="card text-center mb-6">
          <h1 className="text-3xl font-display font-bold text-primary-700 mb-6">
            Assessment Results
          </h1>

          {/* Score Gauge */}
          <div className="relative w-64 h-32 mx-auto mb-8">
            <svg viewBox="0 0 200 100" className="w-full h-full">
              <path
                d="M 20 80 A 80 80 0 0 1 180 80"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="20"
              />
              <path
                d="M 20 80 A 80 80 0 0 1 180 80"
                fill="none"
                stroke={
                  result.label === 'High'
                    ? '#ef4444'
                    : result.label === 'Moderate'
                    ? '#f59e0b'
                    : '#16a34a'
                }
                strokeWidth="20"
                strokeDasharray={`${(result.score / 100) * 251.2} 251.2`}
                strokeLinecap="round"
              />
              <line
                x1="100"
                y1="100"
                x2="100"
                y2="80"
                stroke="#374151"
                strokeWidth="3"
                transform={`rotate(${getGaugeRotation()} 100 100)`}
                transformOrigin="100 100"
              />
            </svg>
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2">
              <div className={`text-4xl font-bold ${getScoreColor()}`}>{result.score}</div>
              <div className="text-lg font-semibold text-gray-700">{result.label} Risk</div>
            </div>
          </div>

          {/* Explanation */}
          {result.explanation && result.explanation.length > 0 && (
            <div className="mt-8 text-left">
              <h2 className="text-xl font-semibold mb-4">Key Factors</h2>
              <div className="flex flex-wrap gap-2">
                {result.explanation.map((item, idx) => (
                  <span
                    key={idx}
                    className="px-4 py-2 bg-primary-100 text-primary-800 rounded-full text-sm font-medium"
                  >
                    {item.feature} ({item.weight.toFixed(2)})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Suggestions */}
        <div className="card mb-6">
          <h2 className="text-xl font-semibold mb-4">Personalized Suggestions</h2>
          <div className="space-y-3">
            {result.suggestions.map((suggestion, idx) => (
              <div key={idx} className="p-4 bg-primary-50 rounded-xl">
                <p className="text-gray-700">{suggestion}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4 justify-center">
          <button onClick={downloadPDF} className="btn-secondary">
            Download PDF
          </button>
          <Link href="/questionnaire" className="btn-primary">
            New Assessment
          </Link>
          <Link href="/dashboard" className="btn-secondary">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}

