'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/auth/AuthProvider'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { BarChart, Clock, Music, TrendingUp, Calendar } from 'lucide-react'

interface PlaySession {
  id: string
  started_at: string
  ended_at: string
  notes_played: number
  config_name?: string
}

interface UserStats {
  total_sessions: number
  total_notes_played: number
  total_time_played: number
  favorite_config: string | null
}

export default function Dashboard() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [sessions, setSessions] = useState<PlaySession[]>([])
  const [stats, setStats] = useState<UserStats | null>(null)
  const [loadingData, setLoadingData] = useState(true)

  useEffect(() => {
    if (!loading && !user) {
      router.push('/')
    }
  }, [user, loading, router])

  useEffect(() => {
    if (user) {
      loadDashboardData()
    }
  }, [user])

  const loadDashboardData = async () => {
    const supabase = createClient()

    // Load recent sessions
    const { data: sessionsData } = await supabase
      .from('play_sessions')
      .select('*')
      .eq('user_id', user!.id)
      .order('started_at', { ascending: false })
      .limit(10)

    if (sessionsData) {
      setSessions(sessionsData)
    }

    // Load user stats
    const { data: statsData } = await supabase
      .from('user_stats')
      .select('*')
      .eq('user_id', user!.id)
      .single()

    if (statsData) {
      setStats(statsData as any)
    }

    setLoadingData(false)
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    })
  }

  if (loading || loadingData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/')}
            className="text-purple-300 hover:text-white mb-4"
          >
            ← Back to Launchpad
          </button>
          <h1 className="text-4xl font-bold text-white mb-2">
            Welcome back, {user.user_metadata?.display_name || 'Music Maker'}!
          </h1>
          <p className="text-purple-200">
            Track your musical journey and see your progress
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 text-white">
            <div className="flex items-center gap-3 mb-2">
              <Calendar className="text-purple-400" size={24} />
              <h3 className="text-sm font-medium text-purple-200">Total Sessions</h3>
            </div>
            <p className="text-3xl font-bold">
              {stats?.total_sessions || 0}
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 text-white">
            <div className="flex items-center gap-3 mb-2">
              <Music className="text-blue-400" size={24} />
              <h3 className="text-sm font-medium text-purple-200">Notes Played</h3>
            </div>
            <p className="text-3xl font-bold">
              {stats?.total_notes_played || 0}
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 text-white">
            <div className="flex items-center gap-3 mb-2">
              <Clock className="text-green-400" size={24} />
              <h3 className="text-sm font-medium text-purple-200">Time Played</h3>
            </div>
            <p className="text-3xl font-bold">
              {formatDuration(stats?.total_time_played || 0)}
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 text-white">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className="text-yellow-400" size={24} />
              <h3 className="text-sm font-medium text-purple-200">Favorite Config</h3>
            </div>
            <p className="text-lg font-bold truncate">
              {stats?.favorite_config || 'None yet'}
            </p>
          </div>
        </div>

        {/* Recent Sessions */}
        <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 text-white">
          <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
            <BarChart size={28} />
            Recent Play Sessions
          </h2>

          {sessions.length === 0 ? (
            <p className="text-purple-200 text-center py-8">
              No sessions yet. Start playing to see your stats!
            </p>
          ) : (
            <div className="space-y-3">
              {sessions.map((session) => {
                const duration = session.ended_at
                  ? Math.floor(
                      (new Date(session.ended_at).getTime() -
                        new Date(session.started_at).getTime()) /
                        1000
                    )
                  : 0

                return (
                  <div
                    key={session.id}
                    className="bg-white/5 rounded-lg p-4 flex items-center justify-between"
                  >
                    <div>
                      <p className="font-medium">
                        {session.config_name || 'Unknown Config'}
                      </p>
                      <p className="text-sm text-purple-300">
                        {formatDate(session.started_at)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">
                        {session.notes_played || 0} notes
                      </p>
                      <p className="text-sm text-purple-300">
                        {formatDuration(duration)}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Call to Action */}
        <div className="mt-8 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-8 text-white text-center">
          <h3 className="text-2xl font-bold mb-2">Ready to make more music?</h3>
          <p className="mb-6 text-purple-100">
            Head back to the launchpad and keep creating!
          </p>
          <button
            onClick={() => router.push('/')}
            className="bg-white text-purple-600 px-8 py-3 rounded-full font-bold hover:bg-purple-100 transition-colors"
          >
            Go to Launchpad
          </button>
        </div>
      </div>
    </div>
  )
}
