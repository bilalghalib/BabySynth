// Core domain types for BabySynth

export interface LaunchpadConfig {
  id?: string
  name: string
  description?: string
  layout: GridLayout
  colors: ColorMap
  audio: AudioConfig
  metadata?: ConfigMetadata
}

export interface GridLayout {
  grid: string[][]  // 9x9 grid of note names or sound identifiers
  scale?: string[]  // Musical scale (e.g., ['C', 'D', 'E', 'F', 'G', 'A', 'B'])
}

export interface ColorMap {
  [note: string]: RGB
}

export type RGB = [number, number, number]

export interface AudioConfig {
  waveform?: Waveform
  envelope?: ADSREnvelope
  effects?: AudioEffects
  volume?: number
}

export type Waveform = 'sine' | 'square' | 'sawtooth' | 'triangle'

export interface ADSREnvelope {
  attack: number   // seconds
  decay: number    // seconds
  sustain: number  // 0-1
  release: number  // seconds
}

export interface AudioEffects {
  reverb?: {
    enabled: boolean
    mix: number      // 0-100
    roomSize: number // 0-100
  }
  delay?: {
    enabled: boolean
    mix: number      // 0-100
    time: number     // seconds
  }
}

export interface ConfigMetadata {
  userId?: string
  isPublic?: boolean
  likesCount?: number
  downloadsCount?: number
  createdAt?: string
  updatedAt?: string
}

// Lesson types
export interface Lesson {
  id: string
  title: string
  description: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  order: number
  instructions: LessonStep[]
  requiredConfig?: string
}

export interface LessonStep {
  instruction: string
  highlightButtons?: [number, number][] // [x, y] coordinates
  expectedNotes?: string[]
  feedback?: {
    success: string
    retry: string
  }
}

// User progress types
export interface UserProgress {
  userId: string
  lessonId: string
  completedAt?: string
  score?: number
  timeSpent?: number // seconds
}

export interface PlaySession {
  id?: string
  userId: string
  configId?: string
  startedAt: string
  endedAt?: string
  notesPlayed?: number
}

// User profile types
export interface UserProfile {
  id: string
  displayName?: string
  avatarUrl?: string
  subscriptionTier: 'free' | 'pro' | 'classroom'
  subscriptionExpiresAt?: string
  createdAt: string
}

// Classroom types (for future use)
export interface Classroom {
  id: string
  name: string
  teacherId: string
  inviteCode: string
  createdAt: string
}

export interface ClassroomStudent {
  classroomId: string
  studentId: string
  joinedAt: string
}
