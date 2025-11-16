'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { VirtualLaunchpad } from '@/components/launchpad'
import { SaveConfigModal } from '@/components/launchpad/SaveConfigModal'
import { allConfigs } from '@/configs'
import type { LaunchpadConfig } from '@/types'
import { AuthModal } from '@/components/auth/AuthModal'
import { UserMenu } from '@/components/auth/UserMenu'
import { useAuth } from '@/lib/auth/AuthProvider'
import { usePlaySession } from '@/hooks/usePlaySession'
import { Save, Store } from 'lucide-react'

export default function Home() {
  const [selectedConfig, setSelectedConfig] = useState<LaunchpadConfig>(allConfigs[0])
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [saveModalOpen, setSaveModalOpen] = useState(false)
  const { user } = useAuth()
  const { trackNotePlay } = usePlaySession(selectedConfig.name)
  const router = useRouter()

  // Load config from marketplace if present
  useEffect(() => {
    const loadedConfig = localStorage.getItem('loadedConfig')
    if (loadedConfig) {
      try {
        const config = JSON.parse(loadedConfig)
        setSelectedConfig(config)
        localStorage.removeItem('loadedConfig')
      } catch (e) {
        console.error('Failed to load config from localStorage', e)
      }
    }
  }, [])

  const handleNotePlay = (note: string, position: [number, number]) => {
    console.log(`Played ${note} at position ${position}`)
    trackNotePlay()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Top Navigation */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex gap-2">
            <button
              onClick={() => router.push('/marketplace')}
              className="flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-full font-medium transition-colors"
            >
              <Store size={20} />
              <span className="hidden sm:inline">Marketplace</span>
            </button>
            {user && (
              <button
                onClick={() => setSaveModalOpen(true)}
                className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-full font-medium transition-colors"
              >
                <Save size={20} />
                <span className="hidden sm:inline">Save Config</span>
              </button>
            )}
          </div>

          <div>
            {user ? (
              <UserMenu />
            ) : (
              <button
                onClick={() => setAuthModalOpen(true)}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-full font-medium transition-colors"
              >
                Sign In
              </button>
            )}
          </div>
        </div>

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
            onNotePlay={handleNotePlay}
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

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />

      {/* Save Config Modal */}
      <SaveConfigModal
        isOpen={saveModalOpen}
        onClose={() => setSaveModalOpen(false)}
        config={selectedConfig}
      />
    </div>
  )
}
