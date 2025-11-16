'use client'

import { useEffect, useRef, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/lib/auth/AuthProvider'

export function usePlaySession(configName: string) {
  const { user } = useAuth()
  const [sessionId, setSessionId] = useState<string | null>(null)
  const notesPlayedRef = useRef(0)
  const supabase = createClient()

  // Start session when component mounts or config changes
  useEffect(() => {
    if (!user) return

    const startSession = async () => {
      const { data, error } = await supabase
        .from('play_sessions')
        .insert({
          user_id: user.id,
          config_name: configName,
          started_at: new Date().toISOString(),
          notes_played: 0,
        })
        .select()
        .single()

      if (data && !error) {
        setSessionId(data.id)
        notesPlayedRef.current = 0
      }
    }

    startSession()

    // End session when unmounting or changing config
    return () => {
      if (sessionId) {
        endSession()
      }
    }
  }, [user, configName])

  const endSession = async () => {
    if (!sessionId) return

    await supabase
      .from('play_sessions')
      .update({
        ended_at: new Date().toISOString(),
        notes_played: notesPlayedRef.current,
      })
      .eq('id', sessionId)
  }

  const trackNotePlay = () => {
    notesPlayedRef.current += 1

    // Periodically update the session (every 10 notes)
    if (notesPlayedRef.current % 10 === 0 && sessionId) {
      supabase
        .from('play_sessions')
        .update({ notes_played: notesPlayedRef.current })
        .eq('id', sessionId)
        .then(() => {})
    }
  }

  return {
    trackNotePlay,
  }
}
