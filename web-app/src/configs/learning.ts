import type { LaunchpadConfig } from '@/types'

export const learningConfig: LaunchpadConfig = {
  name: 'Learning Mode',
  description: 'Learn note names and musical scales',
  layout: {
    grid: [
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
      ['x', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'x'],
      ['x', 'B', 'C', 'D', 'E', 'F', 'G', 'A', 'x'],
      ['x', 'C', 'D', 'E', 'F', 'G', 'A', 'B', 'x'],
      ['x', 'D', 'E', 'F', 'G', 'A', 'B', 'C', 'x'],
      ['x', 'E', 'F', 'G', 'A', 'B', 'C', 'D', 'x'],
      ['x', 'F', 'G', 'A', 'B', 'C', 'D', 'E', 'x'],
      ['x', 'G', 'A', 'B', 'C', 'D', 'E', 'F', 'x'],
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
    ],
    scale: ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
  },
  colors: {
    'C': [255, 50, 50],    // Red (Do)
    'D': [255, 150, 0],    // Orange (Re)
    'E': [255, 255, 0],    // Yellow (Mi)
    'F': [0, 255, 0],      // Green (Fa)
    'G': [0, 150, 255],    // Light Blue (Sol)
    'A': [100, 50, 255],   // Purple (La)
    'B': [255, 100, 200],  // Pink (Ti)
  },
  audio: {
    waveform: 'triangle',
    envelope: {
      attack: 0.1,
      decay: 0.2,
      sustain: 0.7,
      release: 0.3,
    },
    volume: 0.5,
  },
  metadata: {
    isPublic: true,
  }
}
