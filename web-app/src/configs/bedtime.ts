import type { LaunchpadConfig } from '@/types'

export const bedtimeConfig: LaunchpadConfig = {
  name: 'Bedtime Mode',
  description: 'Soft colors and gentle sounds for calming down',
  layout: {
    grid: [
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
      ['x', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'x'],
      ['x', 'C', 'D', 'D', 'D', 'D', 'D', 'C', 'x'],
      ['x', 'C', 'D', 'E', 'E', 'E', 'D', 'C', 'x'],
      ['x', 'C', 'D', 'E', 'E', 'E', 'D', 'C', 'x'],
      ['x', 'C', 'D', 'D', 'D', 'D', 'D', 'C', 'x'],
      ['x', 'C', 'C', 'C', 'C', 'C', 'C', 'C', 'x'],
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
    ],
    scale: ['C', 'D', 'E', 'F', 'G'],
  },
  colors: {
    'C': [30, 50, 100],    // Soft blue
    'D': [50, 70, 120],    // Medium blue
    'E': [70, 90, 140],    // Light blue
    'F': [40, 60, 110],    // Sea blue
    'G': [60, 80, 130],    // Sky blue
  },
  audio: {
    waveform: 'sine',
    envelope: {
      attack: 0.5,
      decay: 1.0,
      sustain: 0.8,
      release: 1.5,
    },
    volume: 0.4,
    effects: {
      reverb: {
        enabled: true,
        mix: 50,
        roomSize: 80,
      }
    }
  },
  metadata: {
    isPublic: true,
  }
}
