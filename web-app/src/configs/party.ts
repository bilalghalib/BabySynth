import type { LaunchpadConfig } from '@/types'

export const partyConfig: LaunchpadConfig = {
  name: 'Party Mode',
  description: 'Bright colors and energetic sounds for celebrations!',
  layout: {
    grid: [
      ['C', 'C', 'C', 'D', 'D', 'D', 'E', 'E', 'x'],
      ['C', 'C', 'C', 'D', 'D', 'D', 'E', 'E', 'x'],
      ['C', 'C', 'C', 'D', 'D', 'D', 'E', 'E', 'x'],
      ['F', 'F', 'F', 'G', 'G', 'G', 'A', 'A', 'x'],
      ['F', 'F', 'F', 'G', 'G', 'G', 'A', 'A', 'x'],
      ['F', 'F', 'F', 'G', 'G', 'G', 'A', 'A', 'x'],
      ['B', 'B', 'B', 'C', 'C', 'C', 'D', 'D', 'x'],
      ['B', 'B', 'B', 'C', 'C', 'C', 'D', 'D', 'x'],
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
    ],
    scale: ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
  },
  colors: {
    'C': [255, 0, 255],    // Bright Magenta
    'D': [255, 255, 0],    // Yellow
    'E': [0, 255, 255],    // Cyan
    'F': [255, 0, 0],      // Red
    'G': [0, 255, 0],      // Green
    'A': [0, 0, 255],      // Blue
    'B': [255, 128, 0],    // Orange
  },
  audio: {
    waveform: 'square',
    envelope: {
      attack: 0.05,
      decay: 0.1,
      sustain: 0.7,
      release: 0.2,
    },
    volume: 0.7,
  },
  metadata: {
    isPublic: true,
  }
}
