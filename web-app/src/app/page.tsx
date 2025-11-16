'use client'

import { useState } from 'react'
import { VirtualLaunchpad } from '@/components/launchpad'
import { allConfigs } from '@/configs'
import type { LaunchpadConfig } from '@/types'

export default function Home() {
  const [selectedConfig, setSelectedConfig] = useState<LaunchpadConfig>(allConfigs[0])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-4">
            🎹 BabySynth
          </h1>
          <p className="text-xl text-purple-200 mb-6">
            Make music with colorful buttons - no hardware required!
          </p>

          {/* Config Selector */}
          <div className="flex flex-wrap gap-3 justify-center mb-8">
            {allConfigs.map((config) => (
              <button
                key={config.name}
                onClick={() => setSelectedConfig(config)}
                className={`px-6 py-3 rounded-full font-medium transition-all ${
                  selectedConfig.name === config.name
                    ? 'bg-purple-500 text-white scale-110 shadow-lg'
                    : 'bg-white/10 text-white hover:bg-white/20'
                }`}
              >
                {config.name}
              </button>
            ))}
          </div>
        </div>

        {/* Virtual Launchpad */}
        <div className="flex justify-center">
          <VirtualLaunchpad
            config={selectedConfig}
            onNotePlay={(note, position) => {
              console.log(`Played ${note} at position ${position}`)
            }}
          />
        </div>

        {/* Instructions */}
        <div className="mt-12 text-center max-w-2xl mx-auto">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 text-white">
            <h2 className="text-2xl font-bold mb-4">How to Play</h2>
            <ul className="text-left space-y-2">
              <li>✨ Click or tap any colored button to play a note</li>
              <li>🎨 Switch between different modes using the buttons above</li>
              <li>🎵 Each color represents a different musical note</li>
              <li>👶 Perfect for babies, toddlers, and music learners!</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-purple-200 text-sm">
          <p>Made with ❤️ for music education</p>
        </div>
      </div>
    </div>
  )
}
