'use client'

import { useState, useCallback, useEffect } from 'react'
import { LaunchpadButton } from './LaunchpadButton'
import { useAudioEngine } from '@/hooks/useAudioEngine'
import type { LaunchpadConfig, RGB } from '@/types'

interface VirtualLaunchpadProps {
  config: LaunchpadConfig
  onNotePlay?: (note: string, position: [number, number]) => void
  highlightPositions?: [number, number][]
  className?: string
}

export function VirtualLaunchpad({
  config,
  onNotePlay,
  highlightPositions = [],
  className = '',
}: VirtualLaunchpadProps) {
  const { playNote, stopNote, isInitialized } = useAudioEngine()
  const [activeButtons, setActiveButtons] = useState<Set<string>>(new Set())

  // Convert position to key for tracking
  const posKey = (x: number, y: number) => `${x},${y}`

  const handleButtonPress = useCallback(
    (x: number, y: number, note?: string) => {
      if (!note || note === 'x') return

      // Play audio
      playNote(note, config.audio)

      // Track active button
      setActiveButtons((prev) => new Set(prev).add(posKey(x, y)))

      // Notify parent component
      onNotePlay?.(note, [x, y])
    },
    [config.audio, playNote, onNotePlay]
  )

  const handleButtonRelease = useCallback(
    (x: number, y: number, note?: string) => {
      if (!note || note === 'x') return

      // Stop audio
      stopNote(note)

      // Remove from active buttons
      setActiveButtons((prev) => {
        const next = new Set(prev)
        next.delete(posKey(x, y))
        return next
      })
    },
    [stopNote]
  )

  // Get color for a specific note
  const getButtonColor = (note: string): RGB => {
    return config.colors[note] || [100, 100, 100] // Default gray
  }

  // Check if position is highlighted
  const isHighlighted = (x: number, y: number) => {
    return highlightPositions.some(([hx, hy]) => hx === x && hy === y)
  }

  return (
    <div className={`flex flex-col items-center gap-4 ${className}`}>
      {/* Audio initialization prompt for iOS */}
      {!isInitialized && (
        <div className="text-sm text-muted-foreground text-center p-4 bg-yellow-50 rounded-lg">
          Tap anywhere to enable audio
        </div>
      )}

      {/* 9x9 Grid */}
      <div
        className="grid gap-2 p-4 bg-slate-900 rounded-xl shadow-2xl"
        style={{
          gridTemplateColumns: 'repeat(9, minmax(0, 1fr))',
          maxWidth: '600px',
          aspectRatio: '1',
        }}
      >
        {config.layout.grid.map((row, y) =>
          row.map((note, x) => {
            const key = posKey(x, y)
            const isActive = activeButtons.has(key)
            const isEmpty = note === 'x' || note === '.'

            if (isEmpty) {
              // Empty button (inactive)
              return (
                <div
                  key={key}
                  className="aspect-square rounded-lg bg-slate-800/50"
                />
              )
            }

            return (
              <LaunchpadButton
                key={key}
                x={x}
                y={y}
                note={note}
                color={getButtonColor(note)}
                isActive={isActive}
                isHighlighted={isHighlighted(x, y)}
                onPress={handleButtonPress}
                onRelease={handleButtonRelease}
              />
            )
          })
        )}
      </div>

      {/* Config info */}
      <div className="text-center">
        <h2 className="text-xl font-bold">{config.name}</h2>
        {config.description && (
          <p className="text-sm text-muted-foreground">{config.description}</p>
        )}
      </div>
    </div>
  )
}
