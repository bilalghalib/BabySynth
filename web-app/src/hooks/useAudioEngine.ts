'use client'

import { useEffect, useRef, useState } from 'react'
import type { AudioConfig, Waveform, ADSREnvelope } from '@/types'

// Standard musical note frequencies (A4 = 440Hz)
const NOTE_FREQUENCIES: Record<string, number> = {
  'C': 261.63,
  'C#': 277.18,
  'D': 293.66,
  'D#': 311.13,
  'E': 329.63,
  'F': 349.23,
  'F#': 369.99,
  'G': 392.00,
  'G#': 415.30,
  'A': 440.00,
  'A#': 466.16,
  'B': 493.88,
}

interface ActiveNote {
  oscillator: OscillatorNode
  gainNode: GainNode
  releaseTimeout?: NodeJS.Timeout
}

const DEFAULT_ENVELOPE: ADSREnvelope = {
  attack: 0.1,
  decay: 0.2,
  sustain: 0.7,
  release: 0.3,
}

export function useAudioEngine() {
  const audioContextRef = useRef<AudioContext | null>(null)
  const activeNotesRef = useRef<Map<string, ActiveNote>>(new Map())
  const [isInitialized, setIsInitialized] = useState(false)
  const [volume, setVolume] = useState(0.5)
  const masterGainRef = useRef<GainNode | null>(null)

  // Initialize Audio Context
  useEffect(() => {
    const initAudioContext = async () => {
      if (typeof window === 'undefined') return

      try {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext
        const context = new AudioContext()
        audioContextRef.current = context

        // Create master gain node for volume control
        const masterGain = context.createGain()
        masterGain.gain.value = volume
        masterGain.connect(context.destination)
        masterGainRef.current = masterGain

        // Resume context on user interaction (required for iOS Safari)
        if (context.state === 'suspended') {
          await context.resume()
        }

        setIsInitialized(true)
      } catch (error) {
        console.error('Failed to initialize Audio Context:', error)
      }
    }

    initAudioContext()

    return () => {
      // Cleanup on unmount
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  // Update master volume
  useEffect(() => {
    if (masterGainRef.current) {
      masterGainRef.current.gain.value = volume
    }
  }, [volume])

  const playNote = (
    noteName: string,
    audioConfig?: AudioConfig
  ) => {
    const context = audioContextRef.current
    const masterGain = masterGainRef.current
    if (!context || !masterGain) {
      console.warn('Audio context not initialized')
      return
    }

    // Resume context if suspended (iOS Safari requirement)
    if (context.state === 'suspended') {
      context.resume()
    }

    const frequency = NOTE_FREQUENCIES[noteName]
    if (!frequency) {
      console.warn(`Unknown note: ${noteName}`)
      return
    }

    // Stop existing note if playing
    stopNote(noteName)

    const waveform = audioConfig?.waveform || 'sine'
    const envelope = audioConfig?.envelope || DEFAULT_ENVELOPE

    // Create oscillator
    const oscillator = context.createOscillator()
    oscillator.type = waveform
    oscillator.frequency.value = frequency

    // Create gain node for ADSR envelope
    const gainNode = context.createGain()
    gainNode.gain.value = 0 // Start at 0

    // Connect nodes: Oscillator -> GainNode -> MasterGain -> Destination
    oscillator.connect(gainNode)
    gainNode.connect(masterGain)

    const now = context.currentTime

    // ADSR Envelope
    // Attack
    gainNode.gain.setValueAtTime(0, now)
    gainNode.gain.linearRampToValueAtTime(1, now + envelope.attack)

    // Decay
    gainNode.gain.linearRampToValueAtTime(
      envelope.sustain,
      now + envelope.attack + envelope.decay
    )

    // Start oscillator
    oscillator.start(now)

    // Store active note
    activeNotesRef.current.set(noteName, { oscillator, gainNode })
  }

  const stopNote = (noteName: string) => {
    const context = audioContextRef.current
    if (!context) return

    const activeNote = activeNotesRef.current.get(noteName)
    if (!activeNote) return

    const { oscillator, gainNode, releaseTimeout } = activeNote

    // Clear any existing release timeout
    if (releaseTimeout) {
      clearTimeout(releaseTimeout)
    }

    const now = context.currentTime
    const releaseTime = 0.3 // Default release time

    // Release: Fade out
    gainNode.gain.cancelScheduledValues(now)
    gainNode.gain.setValueAtTime(gainNode.gain.value, now)
    gainNode.gain.linearRampToValueAtTime(0, now + releaseTime)

    // Stop oscillator after release
    oscillator.stop(now + releaseTime)

    // Remove from active notes after release completes
    const timeout = setTimeout(() => {
      activeNotesRef.current.delete(noteName)
    }, releaseTime * 1000)

    activeNotesRef.current.set(noteName, {
      ...activeNote,
      releaseTimeout: timeout
    })
  }

  const stopAllNotes = () => {
    activeNotesRef.current.forEach((_, noteName) => {
      stopNote(noteName)
    })
  }

  const setMasterVolume = (newVolume: number) => {
    setVolume(Math.max(0, Math.min(1, newVolume)))
  }

  return {
    isInitialized,
    playNote,
    stopNote,
    stopAllNotes,
    volume,
    setMasterVolume,
  }
}
