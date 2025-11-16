'use client'

import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import type { RGB } from '@/types'

interface LaunchpadButtonProps {
  x: number
  y: number
  color: RGB
  note?: string
  isActive?: boolean
  isHighlighted?: boolean
  onPress?: (x: number, y: number, note?: string) => void
  onRelease?: (x: number, y: number, note?: string) => void
}

export function LaunchpadButton({
  x,
  y,
  color,
  note,
  isActive = false,
  isHighlighted = false,
  onPress,
  onRelease,
}: LaunchpadButtonProps) {
  const [isPressed, setIsPressed] = useState(false)

  const handlePointerDown = useCallback(() => {
    setIsPressed(true)
    onPress?.(x, y, note)
  }, [x, y, note, onPress])

  const handlePointerUp = useCallback(() => {
    setIsPressed(false)
    onRelease?.(x, y, note)
  }, [x, y, note, onRelease])

  const handlePointerLeave = useCallback(() => {
    if (isPressed) {
      setIsPressed(false)
      onRelease?.(x, y, note)
    }
  }, [isPressed, x, y, note, onRelease])

  const rgbString = `rgb(${color[0]}, ${color[1]}, ${color[2]})`
  const brightness = isPressed || isActive ? 1.0 : 0.7
  const highlightRing = isHighlighted ? '0 0 0 3px rgba(255, 255, 255, 0.8)' : 'none'

  return (
    <motion.button
      className="relative aspect-square rounded-lg cursor-pointer touch-none select-none"
      style={{
        backgroundColor: rgbString,
        filter: `brightness(${brightness})`,
        boxShadow: `
          inset 0 2px 4px rgba(255, 255, 255, 0.3),
          inset 0 -2px 4px rgba(0, 0, 0, 0.3),
          ${highlightRing}
        `,
      }}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerLeave}
      whileTap={{ scale: 0.95 }}
      animate={{
        scale: isPressed || isActive ? 0.95 : 1,
      }}
      transition={{ duration: 0.05 }}
      aria-label={note ? `Play note ${note}` : `Button ${x},${y}`}
    >
      {/* LED glow effect */}
      {(isPressed || isActive) && (
        <motion.div
          className="absolute inset-0 rounded-lg"
          style={{
            backgroundColor: rgbString,
            filter: 'blur(8px)',
            opacity: 0.6,
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.6 }}
          exit={{ opacity: 0 }}
        />
      )}

      {/* Note label (for development/debugging) */}
      {note && process.env.NODE_ENV === 'development' && (
        <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white/70">
          {note}
        </span>
      )}
    </motion.button>
  )
}
