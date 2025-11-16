import type { LaunchpadConfig } from '@/types'

export const drumsConfig: LaunchpadConfig = {
  name: 'Drum Kit',
  description: 'Percussion sounds for rhythm and beats',
  layout: {
    grid: [
      ['C', 'C', 'C', 'D', 'D', 'D', 'E', 'E', 'x'],
      ['C', 'C', 'C', 'D', 'D', 'D', 'E', 'E', 'x'],
      ['C', 'C', 'C', 'D', 'D', 'D', 'E', 'E', 'x'],
      ['F', 'F', 'F', 'G', 'G', 'G', 'A', 'A', 'x'],
      ['F', 'F', 'F', 'G', 'G', 'G', 'A', 'A', 'x'],
      ['F', 'F', 'F', 'G', 'G', 'G', 'A', 'A', 'x'],
      ['B', 'B', 'B', 'C#', 'C#', 'C#', 'D#', 'D#', 'x'],
      ['B', 'B', 'B', 'C#', 'C#', 'C#', 'D#', 'D#', 'x'],
      ['x', 'x', 'x', 'x', 'x', 'x', 'x', 'x', 'x'],
    ],
    scale: ['C', 'C#', 'D', 'D#', 'E', 'F', 'G', 'A', 'B'],
  },
  colors: {
    // Kick drum - low notes
    'C': [200, 0, 0],      // Dark Red
    'D': [150, 0, 0],      // Darker Red

    // Snare - mid notes
    'E': [0, 200, 0],      // Dark Green
    'F': [0, 150, 0],      // Darker Green

    // Hi-hat - high notes
    'G': [200, 200, 0],    // Dark Yellow
    'A': [150, 150, 0],    // Darker Yellow

    // Toms
    'B': [0, 0, 200],      // Dark Blue
    'C#': [150, 0, 150],   // Purple
    'D#': [0, 150, 150],   // Teal
  },
  audio: {
    waveform: 'sawtooth',
    envelope: {
      attack: 0.01,
      decay: 0.1,
      sustain: 0.3,
      release: 0.1,
    },
    volume: 0.8,
  },
  metadata: {
    isPublic: true,
  }
}
