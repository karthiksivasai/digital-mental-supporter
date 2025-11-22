'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'

export default function Home() {
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const [isHydrated, setIsHydrated] = useState(false)

  // Hydrate auth store on mount
  useEffect(() => {
    useAuthStore.persist.rehydrate()
    setIsHydrated(true)
  }, [])

  useEffect(() => {
    if (!isHydrated) return
    
    if (isAuthenticated) {
      router.push('/dashboard')
    } else {
      router.push('/auth/login')
    }
  }, [isAuthenticated, isHydrated, router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-700"></div>
    </div>
  )
}

