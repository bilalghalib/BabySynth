'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth/AuthProvider'
import { createClient } from '@/lib/supabase/client'
import { X } from 'lucide-react'
import type { LaunchpadConfig } from '@/types'

interface SaveConfigModalProps {
  isOpen: boolean
  onClose: () => void
  config: LaunchpadConfig
}

export function SaveConfigModal({ isOpen, onClose, config }: SaveConfigModalProps) {
  const { user } = useAuth()
  const [name, setName] = useState(config.name)
  const [description, setDescription] = useState(config.description || '')
  const [isPublic, setIsPublic] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  if (!isOpen) return null

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!user) {
      setError('You must be signed in to save configs')
      return
    }

    setSaving(true)
    setError('')

    const supabase = createClient()

    const { error: saveError } = await supabase.from('configs').insert({
      user_id: user.id,
      name,
      description,
      config_data: {
        name,
        description,
        layout: config.layout,
        colors: config.colors,
        audio: config.audio,
      },
      is_public: isPublic,
    })

    if (saveError) {
      setError(saveError.message)
      setSaving(false)
    } else {
      onClose()
      setSaving(false)
      alert('Config saved successfully!')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-2xl max-w-md w-full p-8 relative">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X size={24} />
        </button>

        {/* Header */}
        <h2 className="text-3xl font-bold mb-2 text-gray-900 dark:text-white">
          Save Configuration
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Save this config to your account and optionally share it with the community
        </p>

        {/* Error message */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
              Configuration Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
              placeholder="My Awesome Config"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent bg-white dark:bg-slate-700 text-gray-900 dark:text-white"
              placeholder="Describe your configuration..."
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="isPublic"
              checked={isPublic}
              onChange={(e) => setIsPublic(e.target.checked)}
              className="w-4 h-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
            />
            <label htmlFor="isPublic" className="text-sm text-gray-900 dark:text-white">
              Share with the community (make public)
            </label>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white px-6 py-3 rounded-full font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 bg-purple-600 text-white px-6 py-3 rounded-full font-medium hover:bg-purple-700 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Config'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
