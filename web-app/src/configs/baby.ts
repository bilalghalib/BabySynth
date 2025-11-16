import type { LaunchpadConfig } from '@/types'

export const babyConfig: LaunchpadConfig = {
  name: 'Baby Mode',
  description: 'Simple, colorful buttons perfect for little ones',
  layout: {
    grid: [
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
      ['x', 'C', 'C', 'C', 'D', 'D', 'D', 'E', 'x'],
      ['x', 'C', 'C', 'C', 'D', 'D', 'D', 'E', 'x'],
      ['x', 'C', 'C', 'C', 'D', 'D', 'D', 'E', 'x'],
      ['x', 'F', 'F', 'F', 'G', 'G', 'G', 'A', 'x'],
      ['x', 'F', 'F', 'F', 'G', 'G', 'G', 'A', 'x'],
      ['x', 'F', 'F', 'F', 'G', 'G', 'G', 'A', 'x'],
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
    ],
    scale: ['C', 'D', 'E', 'F', 'G', 'A'],
  },
  colors: {
    'C': [255, 0, 0],     // Red
    'D': [0, 255, 0],     // Green
    'E': [0, 0, 255],     // Blue
    'F': [255, 255, 0],   // Yellow
    'G': [255, 0, 255],   // Magenta
    'A': [0, 255, 255],   // Cyan
  },
  audio: {
    waveform: 'sine',
    envelope: {
      attack: 0.1,
      decay: 0.2,
      sustain: 0.8,
      release: 0.3,
    },
    volume: 0.6,
  },
  metadata: {
    isPublic: true,
  }
}
