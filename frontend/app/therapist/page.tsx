'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { therapistApi } from '@/lib/api'
import Nav from '@/components/Nav'
import toast from 'react-hot-toast'
import jsPDF from 'jspdf'

interface Question {
  id: string
  question: string
  type: string
  category?: string
  scale_range?: [number, number]
}

interface Message {
  id: string
  type: 'therapist' | 'user'
  content: string
  timestamp: Date
}

interface Answer {
  question_id: string
  answer: any
  text_response?: string
}

interface WellbeingPlan {
  daily_tasks: string[]
  lifestyle_habits: string[]
  food_suggestions: string[]
  sleep_hygiene: string[]
  stress_reduction: string[]
  physical_activity: string[]
  journaling_prompts: string[]
  screen_time: string[]
  social_connection: string[]
}

export default function TherapistPage() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [currentAnswer, setCurrentAnswer] = useState<any>(null)
  const [textAnswer, setTextAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [totalQuestions] = useState(10)
  const [answers, setAnswers] = useState<Map<string, any>>(new Map())
  const [finalPlan, setFinalPlan] = useState<any>(null)
  const [showPlan, setShowPlan] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
      return
    }
    startSession()
  }, [isAuthenticated, router])

  useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  useEffect(() => {
    if (currentQuestion && inputRef.current) {
      inputRef.current.focus()
    }
  }, [currentQuestion])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const addMessage = (type: 'therapist' | 'user', content: string) => {
    setMessages(prev => [...prev, {
      id: Date.now().toString() + Math.random(),
      type,
      content,
      timestamp: new Date()
    }])
  }

  const simulateTyping = (callback: () => void, delay: number = 1500) => {
    setIsTyping(true)
    setTimeout(() => {
      setIsTyping(false)
      callback()
    }, delay)
  }

  const startSession = async () => {
    setLoading(true)
    try {
      const response = await therapistApi.startSession()
      setSessionId(response.session_id)
      
      // Add welcome message
      addMessage('therapist', "Hello! I'm here to help you create a personalized wellbeing plan. Let's start with a few questions.")
      
      // Show first question with typing animation
      simulateTyping(() => {
        if (response.questions && response.questions.length > 0) {
          const firstQ = response.questions[0]
          addMessage('therapist', firstQ.question)
          setCurrentQuestion(firstQ)
          setCurrentQuestionIndex(1)
        }
      }, 1000)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start session')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswer = async () => {
    if (!sessionId || !currentQuestion) return

    // Validate answer
    if (currentQuestion.type === 'text' && !textAnswer.trim()) {
      toast.error('Please provide an answer')
      return
    }

    if (currentQuestion.type === 'scale' && (currentAnswer === null || currentAnswer === undefined)) {
      toast.error('Please select a value')
      return
    }

    setLoading(true)

    // Format answer text for display
    const answerText = currentQuestion.type === 'scale'
      ? `${currentAnswer}/10`
      : textAnswer
    
    // Add user message
    addMessage('user', answerText)

    // Store answer
    const answerMap = new Map(answers)
    answerMap.set(currentQuestion.id, currentQuestion.type === 'scale' ? currentAnswer : textAnswer)
    setAnswers(answerMap)

    // Clear inputs
    setCurrentAnswer(null)
    setTextAnswer('')
    setCurrentQuestion(null)

    try {
      // Submit answer
      const answer: Answer = {
        question_id: currentQuestion.id,
        answer: currentQuestion.type === 'scale' ? currentAnswer : textAnswer,
        text_response: currentQuestion.type === 'text' ? textAnswer : undefined
      }

      const response = await therapistApi.submitAnswers(sessionId, [answer])
      
      // Check if we're done
      if (response.next_questions && response.next_questions.length === 0) {
        // All questions answered - generate final plan
        simulateTyping(() => {
          addMessage('therapist', "Thank you for sharing all that information. I'm creating your personalized wellbeing plan...")
          generateFinalPlan()
        }, 1500)
      } else {
        // Show next question
        const nextIndex = currentQuestionIndex + 1
        setCurrentQuestionIndex(nextIndex)
        
        simulateTyping(() => {
          if (response.next_questions && response.next_questions.length > 0) {
            const nextQ = response.next_questions[0]
            addMessage('therapist', nextQ.question)
            setCurrentQuestion(nextQ)
          }
        }, 1200)
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to submit answer')
      // Restore question on error
      setCurrentQuestion(currentQuestion)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!loading && currentQuestion) {
        handleAnswer()
      }
    }
  }

  const generateFinalPlan = async () => {
    if (!sessionId) return

    setLoading(true)
    try {
      const response = await therapistApi.getFinalPlan(sessionId)
      setFinalPlan(response)
      setShowPlan(true)

      simulateTyping(() => {
        addMessage('therapist', `Great! I've created your personalized wellbeing plan. Your overall wellbeing score is ${(response.wellbeing_score * 100).toFixed(0)}%. Scroll down to see your comprehensive plans.`)
      }, 1000)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate plan')
    } finally {
      setLoading(false)
    }
  }

  const downloadPlanPDF = () => {
    if (!finalPlan) return

    const doc = new jsPDF()
    let yPos = 20

    doc.setFontSize(18)
    doc.text('Your Personalized Wellbeing Plan', 105, yPos, { align: 'center' })
    yPos += 15

    doc.setFontSize(12)
    doc.text(`Wellbeing Score: ${(finalPlan.wellbeing_score * 100).toFixed(0)}%`, 20, yPos)
    yPos += 7
    doc.text(`Risk Category: ${finalPlan.risk_category}`, 20, yPos)
    yPos += 15

    const plans = [
      { title: '1 Week Plan', plan: finalPlan.one_week_plan },
      { title: '1 Month Plan', plan: finalPlan.one_month_plan },
      { title: '3 Month Plan', plan: finalPlan.three_month_plan },
      { title: '6 Month Plan', plan: finalPlan.six_month_plan }
    ]

    plans.forEach(({ title, plan }) => {
      if (yPos > 270) {
        doc.addPage()
        yPos = 20
      }

      doc.setFontSize(14)
      doc.text(title, 20, yPos)
      yPos += 10

      doc.setFontSize(10)
      const sections = [
        { name: 'Daily Tasks', items: plan.daily_tasks },
        { name: 'Lifestyle Habits', items: plan.lifestyle_habits },
        { name: 'Food Suggestions', items: plan.food_suggestions },
        { name: 'Sleep Hygiene', items: plan.sleep_hygiene },
        { name: 'Stress Reduction', items: plan.stress_reduction },
        { name: 'Physical Activity', items: plan.physical_activity },
        { name: 'Journaling Prompts', items: plan.journaling_prompts },
        { name: 'Screen Time', items: plan.screen_time },
        { name: 'Social Connection', items: plan.social_connection }
      ]

      sections.forEach(section => {
        if (section.items.length > 0) {
          if (yPos > 270) {
            doc.addPage()
            yPos = 20
          }
          doc.setFontSize(11)
          doc.text(section.name + ':', 20, yPos)
          yPos += 7
          doc.setFontSize(9)
          section.items.forEach(item => {
            if (yPos > 270) {
              doc.addPage()
              yPos = 20
            }
            doc.text(`• ${item}`, 25, yPos)
            yPos += 6
          })
          yPos += 3
        }
      })
      yPos += 5
    })

    doc.save('wellbeing-plan.pdf')
    toast.success('Plan downloaded as PDF!')
  }

  const renderQuestionInput = () => {
    if (!currentQuestion) return null

    if (currentQuestion.type === 'scale') {
      const [min, max] = currentQuestion.scale_range || [1, 10]
      return (
        <div className="space-y-4">
          <div className="flex justify-between text-sm text-gray-500 mb-2">
            <span>{min}</span>
            <span>{max}</span>
          </div>
          <input
            type="range"
            min={min}
            max={max}
            value={currentAnswer ?? min}
            onChange={(e) => setCurrentAnswer(parseInt(e.target.value))}
            className="w-full h-2 bg-gradient-to-r from-blue-200 to-purple-200 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
          <div className="text-center">
            <span className="text-3xl font-bold text-blue-600">{currentAnswer ?? min}</span>
            <span className="text-gray-400 ml-2">/ {max}</span>
          </div>
        </div>
      )
    }

    // Text input
    return (
      <textarea
        ref={inputRef}
        value={textAnswer}
        onChange={(e) => setTextAnswer(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Type your answer here..."
        className="w-full px-4 py-3 border-2 border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-400 focus:border-blue-400 resize-none transition-all duration-200 bg-white"
        rows={3}
      />
    )
  }

  if (!isAuthenticated) return null

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <Nav />
      
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        {/* Progress Bar */}
        {!showPlan && (
          <div className="mb-6 bg-white rounded-2xl shadow-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-600">Progress</span>
              <span className="text-sm font-semibold text-blue-600">
                Question {currentQuestionIndex} of {totalQuestions}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${(currentQuestionIndex / totalQuestions) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Chat Container */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col" style={{ height: showPlan ? 'auto' : 'calc(100vh - 250px)' }}>
          <div
            ref={chatContainerRef}
            className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-white to-blue-50/30"
            style={{ maxHeight: showPlan ? 'none' : 'calc(100vh - 350px)' }}
          >
            {messages.map((msg, idx) => (
              <div
                key={msg.id}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                style={{ animationDelay: `${idx * 0.1}s` }}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-5 py-3 shadow-md ${
                    msg.type === 'user'
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-none'
                      : 'bg-white text-gray-800 border border-gray-100 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start animate-fadeIn">
                <div className="bg-white rounded-2xl rounded-bl-none px-5 py-3 shadow-md border border-gray-100">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          {currentQuestion && !showPlan && (
            <div className="p-6 bg-white border-t border-gray-100">
              <div className="mb-4">
                {renderQuestionInput()}
              </div>
              <button
                onClick={handleAnswer}
                disabled={loading || (currentQuestion.type === 'text' && !textAnswer.trim()) || (currentQuestion.type === 'scale' && currentAnswer === null)}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-3 px-6 rounded-xl font-medium hover:from-blue-600 hover:to-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
              >
                {loading ? 'Processing...' : 'Send Answer'}
              </button>
            </div>
          )}
        </div>

        {/* Final Plan Display */}
        {showPlan && finalPlan && (
          <div className="mt-6 space-y-6 animate-fadeIn">
            <div className="bg-white rounded-2xl shadow-2xl p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Your Personalized Wellbeing Plan
                </h2>
                <button
                  onClick={downloadPlanPDF}
                  className="px-5 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl hover:from-green-600 hover:to-emerald-600 transition-all shadow-lg hover:shadow-xl"
                >
                  📥 Download PDF
                </button>
              </div>

              {/* Plan Cards */}
              <div className="space-y-4">
                {[
                  { title: '1 Week Plan', plan: finalPlan.one_week_plan, icon: '📅' },
                  { title: '1 Month Plan', plan: finalPlan.one_month_plan, icon: '📆' },
                  { title: '3 Month Plan', plan: finalPlan.three_month_plan, icon: '🗓️' },
                  { title: '6 Month Plan', plan: finalPlan.six_month_plan, icon: '📋' }
                ].map(({ title, plan, icon }) => (
                  <PlanCard key={title} title={title} plan={plan} icon={icon} />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.4s ease-out forwards;
        }
      `}</style>
    </div>
  )
}

// Plan Card Component
function PlanCard({ title, plan, icon }: { title: string; plan: WellbeingPlan; icon: string }) {
  const [isOpen, setIsOpen] = useState(false)

  const sections = [
    { name: 'Daily Tasks', items: plan.daily_tasks, emoji: '✅' },
    { name: 'Sleep Routine', items: plan.sleep_hygiene, emoji: '😴' },
    { name: 'Stress Reduction', items: plan.stress_reduction, emoji: '🧘' },
    { name: 'Food & Lifestyle', items: plan.food_suggestions, emoji: '🥗' },
    { name: 'Physical Activity', items: plan.physical_activity, emoji: '🏃' },
    { name: 'Journaling Prompts', items: plan.journaling_prompts, emoji: '📝' },
    { name: 'Screen Time', items: plan.screen_time, emoji: '📱' },
    { name: 'Social Connection', items: plan.social_connection, emoji: '👥' },
    { name: 'Lifestyle Habits', items: plan.lifestyle_habits, emoji: '🌟' }
  ]

  return (
    <div className="border-2 border-gray-200 rounded-xl overflow-hidden hover:border-blue-300 transition-all duration-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 bg-gradient-to-r from-blue-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 flex justify-between items-center transition-all"
      >
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{icon}</span>
          <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
        </div>
        <span className={`text-2xl transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}>
          ▼
        </span>
      </button>
      
      {isOpen && (
        <div className="p-6 bg-white animate-fadeIn">
          <div className="grid md:grid-cols-2 gap-4">
            {sections.map((section) => 
              section.items.length > 0 && (
                <div key={section.name} className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-700 mb-2 flex items-center">
                    <span className="mr-2">{section.emoji}</span>
                    {section.name}
                  </h4>
                  <ul className="space-y-1 text-sm text-gray-600">
                    {section.items.map((item, idx) => (
                      <li key={idx} className="flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  )
}
