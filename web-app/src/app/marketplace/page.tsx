'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { Heart, Download, Search, TrendingUp } from 'lucide-react'
import type { LaunchpadConfig } from '@/types'

interface ConfigWithMetadata extends LaunchpadConfig {
  id: string
  user_id: string
  likes_count: number
  downloads_count: number
  is_liked?: boolean
  author_name?: string
}

export default function Marketplace() {
  const router = useRouter()
  const [configs, setConfigs] = useState<ConfigWithMetadata[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filter, setFilter] = useState<'trending' | 'recent' | 'popular'>('trending')

  useEffect(() => {
    loadConfigs()
  }, [filter])

  const loadConfigs = async () => {
    setLoading(true)
    const supabase = createClient()

    let query = supabase
      .from('configs')
      .select(`
        id,
        name,
        description,
        config_data,
        likes_count,
        downloads_count,
        user_id,
        created_at,
        profiles:user_id (display_name)
      `)
      .eq('is_public', true)

    // Apply sorting based on filter
    if (filter === 'trending') {
      query = query.order('likes_count', { ascending: false })
    } else if (filter === 'popular') {
      query = query.order('downloads_count', { ascending: false })
    } else {
      query = query.order('created_at', { ascending: false })
    }

    query = query.limit(20)

    const { data, error } = await query

    if (data && !error) {
      const configsWithData = data.map((item: any) => ({
        id: item.id,
        user_id: item.user_id,
        name: item.name || item.config_data.name,
        description: item.description || item.config_data.description,
        layout: item.config_data.layout,
        colors: item.config_data.colors,
        audio: item.config_data.audio,
        metadata: {
          ...item.config_data.metadata,
          likesCount: item.likes_count,
          downloadsCount: item.downloads_count,
        },
        likes_count: item.likes_count,
        downloads_count: item.downloads_count,
        author_name: item.profiles?.display_name || 'Anonymous',
      }))
      setConfigs(configsWithData)
    }

    setLoading(false)
  }

  const handleLike = async (configId: string) => {
    const supabase = createClient()
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
      alert('Please sign in to like configs')
      return
    }

    // Check if already liked
    const { data: existingLike } = await supabase
      .from('config_likes')
      .select('id')
      .eq('config_id', configId)
      .eq('user_id', user.id)
      .single()

    if (existingLike) {
      // Unlike
      await supabase
        .from('config_likes')
        .delete()
        .eq('config_id', configId)
        .eq('user_id', user.id)
    } else {
      // Like
      await supabase
        .from('config_likes')
        .insert({ config_id: configId, user_id: user.id })
    }

    // Reload configs to update like counts
    loadConfigs()
  }

  const handleLoad = async (config: ConfigWithMetadata) => {
    const supabase = createClient()

    // Increment download count
    await supabase.rpc('increment_downloads', { config_id: config.id })

    // Store config in localStorage for the main page
    localStorage.setItem('loadedConfig', JSON.stringify(config))

    // Navigate to home page
    router.push('/?loaded=true')
  }

  const filteredConfigs = configs.filter(config =>
    config.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    config.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/')}
            className="text-purple-300 hover:text-white mb-4"
          >
            ← Back to Launchpad
          </button>
          <h1 className="text-4xl font-bold text-white mb-2">
            Config Marketplace
          </h1>
          <p className="text-purple-200">
            Discover and download community-created configurations
          </p>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search configs..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-white/10 backdrop-blur-lg border border-white/20 rounded-full text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setFilter('trending')}
              className={`px-6 py-3 rounded-full font-medium transition-all ${
                filter === 'trending'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/10 text-white hover:bg-white/20'
              }`}
            >
              <TrendingUp size={20} className="inline mr-2" />
              Trending
            </button>
            <button
              onClick={() => setFilter('popular')}
              className={`px-6 py-3 rounded-full font-medium transition-all ${
                filter === 'popular'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/10 text-white hover:bg-white/20'
              }`}
            >
              Popular
            </button>
            <button
              onClick={() => setFilter('recent')}
              className={`px-6 py-3 rounded-full font-medium transition-all ${
                filter === 'recent'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/10 text-white hover:bg-white/20'
              }`}
            >
              Recent
            </button>
          </div>
        </div>

        {/* Configs Grid */}
        {loading ? (
          <div className="text-center text-white py-12">Loading configs...</div>
        ) : filteredConfigs.length === 0 ? (
          <div className="text-center text-purple-200 py-12">
            <p className="text-xl mb-4">No configs found</p>
            <p>Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredConfigs.map((config) => (
              <div
                key={config.id}
                className="bg-white/10 backdrop-blur-lg rounded-xl p-6 text-white hover:bg-white/15 transition-all"
              >
                <h3 className="text-xl font-bold mb-2">{config.name}</h3>
                <p className="text-purple-200 text-sm mb-4 line-clamp-2">
                  {config.description || 'No description'}
                </p>

                <div className="flex items-center gap-2 text-sm text-purple-300 mb-4">
                  <span>by {config.author_name}</span>
                </div>

                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4 text-sm">
                    <span className="flex items-center gap-1">
                      <Heart size={16} />
                      {config.likes_count}
                    </span>
                    <span className="flex items-center gap-1">
                      <Download size={16} />
                      {config.downloads_count}
                    </span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleLoad(config)}
                    className="flex-1 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-full font-medium transition-colors"
                  >
                    Load Config
                  </button>
                  <button
                    onClick={() => handleLike(config.id)}
                    className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-full transition-colors"
                  >
                    <Heart size={20} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
