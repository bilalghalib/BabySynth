# BabySynth Web - Technical Architecture

**Version:** 1.0
**Last Updated:** 2025-11-16

---

## 1. System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Devices                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  iPhone  │  │   iPad   │  │  Chrome  │  │ Desktop  │   │
│  │  Safari  │  │  Safari  │  │  Browser │  │  Bridge  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │     Vercel Edge Network     │
        │   (CDN + Edge Functions)    │
        └─────────────┬───────────────┘
                      │
        ┌─────────────┴───────────────┐
        │                             │
        ▼                             ▼
┌───────────────┐            ┌────────────────┐
│   Next.js 14  │            │   Supabase     │
│   App Router  │◄──────────►│                │
│               │            │  - Auth        │
│  - React 18   │            │  - Postgres    │
│  - Tailwind   │            │  - Storage     │
│  - Shadcn/ui  │            │  - Realtime    │
│  - Web Audio  │            │  - Edge Fns    │
└───────────────┘            └────────────────┘
        │                             │
        └─────────────┬───────────────┘
                      │
                      ▼
              ┌───────────────┐
              │     Stripe    │
              │  (Payments)   │
              └───────────────┘
```

---

## 2. Technology Stack

### Frontend

#### Core Framework
```json
{
  "framework": "Next.js 14",
  "version": "14.0.4",
  "features": [
    "App Router (RSC)",
    "Server Actions",
    "Streaming SSR",
    "Image Optimization",
    "Font Optimization"
  ]
}
```

**Why Next.js 14?**
- ✅ Best React framework for production
- ✅ Built-in optimization (images, fonts, code splitting)
- ✅ Server Actions eliminate API boilerplate
- ✅ Excellent Vercel deployment
- ✅ Strong ecosystem

#### UI Layer
```json
{
  "styling": "TailwindCSS v3",
  "components": "shadcn/ui",
  "icons": "lucide-react",
  "animations": "framer-motion",
  "canvas": "HTML5 Canvas API"
}
```

**Component Library Choice:**
- **shadcn/ui** over Material-UI or Chakra
  - Copy-paste, not dependency
  - Full customization
  - Tailwind-based
  - Accessible by default
  - Smaller bundle size

#### Audio Engine
```javascript
{
  "api": "Web Audio API",
  "polyfill": "standardized-audio-context",
  "synth": "Custom OscillatorNode-based",
  "samples": "Optional WAV files via Supabase Storage"
}
```

**Audio Architecture:**
```typescript
class AudioEngine {
  private audioContext: AudioContext;
  private gainNode: GainNode;
  private activeNotes: Map<string, OscillatorNode>;

  // Frequency map
  private frequencies = {
    C: 261.63,
    D: 293.66,
    // ... etc
  };

  // ADSR envelope
  applyEnvelope(gain: GainNode, config: ADSRConfig) {
    const now = audioContext.currentTime;
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(1, now + config.attack);
    // ... decay, sustain, release
  }
}
```

#### State Management
```typescript
{
  "global": "React Context + useReducer",
  "server": "Next.js Server Components",
  "realtime": "Supabase Realtime",
  "form": "React Hook Form + Zod",
  "cache": "React Query / SWR"
}
```

**State Architecture:**
- `AudioContext` - Web Audio state
- `UserContext` - Auth state (Supabase)
- `ConfigContext` - Current config/theme
- `LessonContext` - Progress tracking
- Server Components for static data
- Client Components for interactive UI

---

### Backend

#### Database & Auth: Supabase
```typescript
{
  "database": "PostgreSQL 15",
  "auth": "Supabase Auth (JWT)",
  "storage": "Supabase Storage (S3-compatible)",
  "realtime": "Postgres CDC + WebSockets",
  "functions": "Deno Edge Functions"
}
```

**Supabase Services Used:**

1. **Auth**
   - Email/password
   - OAuth (Google, Apple)
   - Magic links
   - JWT tokens (auto-managed)

2. **Database**
   - Row Level Security (RLS)
   - Real-time subscriptions
   - Full-text search
   - JSONB for flexible schemas

3. **Storage**
   - Audio samples (.wav files)
   - Config exports (.json)
   - User avatars
   - Lesson media

4. **Edge Functions**
   - Stripe webhook handler
   - Email notifications
   - Admin operations
   - Analytics

#### API Layer
```typescript
// Server Actions (no API routes needed!)
'use server'

export async function saveConfig(config: ConfigData) {
  const supabase = createServerClient();
  const { data, error } = await supabase
    .from('configs')
    .insert({
      user_id: (await supabase.auth.getUser()).data.user?.id,
      config_data: config,
    });

  return { data, error };
}
```

**Why Server Actions over API Routes?**
- ✅ Less boilerplate
- ✅ Type-safe by default
- ✅ Auto CSRF protection
- ✅ Streaming support
- ✅ Co-located with components

---

### Deployment

#### Hosting: Vercel
```yaml
Production:
  url: babysynth.com
  region: auto (edge)
  functions: edge

Preview:
  url: *.vercel.app
  per-branch: true

Environment:
  NODE_ENV: production
  NEXT_PUBLIC_SUPABASE_URL: env.SUPABASE_URL
  NEXT_PUBLIC_SUPABASE_ANON_KEY: env.SUPABASE_ANON_KEY
  SUPABASE_SERVICE_ROLE_KEY: env.SUPABASE_SERVICE_KEY
  STRIPE_SECRET_KEY: env.STRIPE_SECRET
```

**Vercel Features Used:**
- Edge Functions (low latency)
- Image Optimization
- Font Optimization
- Analytics
- Web Vitals tracking
- Preview deployments (per PR)

---

## 3. Data Architecture

### Database Schema (Supabase Postgres)

```sql
-- Users (managed by Supabase Auth)
auth.users (
  id uuid PRIMARY KEY,
  email text,
  created_at timestamp
)

-- User Profiles
public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users,
  display_name text,
  avatar_url text,
  subscription_tier text DEFAULT 'free',
  subscription_expires_at timestamp,
  created_at timestamp DEFAULT now(),
  updated_at timestamp DEFAULT now()
)

-- Configurations
public.configs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  config_data jsonb NOT NULL,
  is_public boolean DEFAULT false,
  likes_count int DEFAULT 0,
  downloads_count int DEFAULT 0,
  created_at timestamp DEFAULT now(),
  updated_at timestamp DEFAULT now(),

  -- Indexes
  INDEX idx_configs_user (user_id),
  INDEX idx_configs_public (is_public, likes_count DESC),
  INDEX idx_configs_search (name, description)
)

-- Config Likes (many-to-many)
public.config_likes (
  user_id uuid REFERENCES auth.users ON DELETE CASCADE,
  config_id uuid REFERENCES configs ON DELETE CASCADE,
  created_at timestamp DEFAULT now(),

  PRIMARY KEY (user_id, config_id)
)

-- Lessons
public.lessons (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  order_index int NOT NULL,
  title text NOT NULL,
  description text,
  instructions jsonb NOT NULL, -- Steps array
  required_config jsonb, -- Optional specific config
  unlock_after uuid REFERENCES lessons, -- Previous lesson
  is_premium boolean DEFAULT false,
  created_at timestamp DEFAULT now()
)

-- User Progress
public.user_progress (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users ON DELETE CASCADE,
  lesson_id uuid REFERENCES lessons ON DELETE CASCADE,
  completed_at timestamp,
  score int,
  time_spent int, -- seconds
  created_at timestamp DEFAULT now(),

  UNIQUE (user_id, lesson_id)
)

-- Play Sessions (analytics)
public.play_sessions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users ON DELETE CASCADE,
  config_id uuid REFERENCES configs,
  started_at timestamp DEFAULT now(),
  ended_at timestamp,
  notes_played int DEFAULT 0,
  duration int -- seconds
)

-- Classrooms (for teachers)
public.classrooms (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  teacher_id uuid REFERENCES auth.users ON DELETE CASCADE,
  name text NOT NULL,
  join_code text UNIQUE NOT NULL,
  max_students int DEFAULT 30,
  created_at timestamp DEFAULT now()
)

-- Classroom Students
public.classroom_students (
  classroom_id uuid REFERENCES classrooms ON DELETE CASCADE,
  student_id uuid REFERENCES auth.users ON DELETE CASCADE,
  joined_at timestamp DEFAULT now(),

  PRIMARY KEY (classroom_id, student_id)
)

-- Row Level Security Policies
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
-- ... etc

-- Example RLS Policy
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Public configs are viewable by all"
  ON configs FOR SELECT
  USING (is_public = true OR user_id = auth.uid());
```

### JSONB Schemas

#### Config Data Structure
```typescript
interface ConfigData {
  version: string; // "1.0"

  // Grid layout (9x9)
  layout: {
    model: string;
    grid: string[][]; // 9x9 array of note names or 'x'
  };

  // Note colors
  colors: {
    [noteName: string]: [number, number, number]; // RGB
  };

  // Audio settings
  audio: {
    waveform?: 'sine' | 'square' | 'triangle' | 'sawtooth';
    envelope?: {
      attack: number;
      decay: number;
      sustain: number;
      release: number;
    };
  };

  // Optional animations
  animations?: {
    [name: string]: AnimationData;
  };

  // Optional themes
  themes?: {
    [name: string]: ThemeData;
  };
}
```

#### Lesson Instructions
```typescript
interface LessonInstructions {
  steps: Array<{
    type: 'instruction' | 'action' | 'feedback';
    text: string;
    highlight?: { x: number; y: number }; // Button to highlight
    expectedAction?: {
      button: { x: number; y: number };
      note: string;
    };
    successMessage?: string;
    tryAgainMessage?: string;
  }>;
}
```

---

## 4. Component Architecture

### File Structure
```
web-app/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx
│   │   ├── signup/
│   │   │   └── page.tsx
│   │   └── layout.tsx
│   │
│   ├── (app)/
│   │   ├── play/
│   │   │   └── page.tsx          # Main Launchpad
│   │   ├── lessons/
│   │   │   ├── page.tsx          # Lesson list
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Lesson player
│   │   ├── marketplace/
│   │   │   ├── page.tsx          # Browse configs
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Config detail
│   │   ├── dashboard/
│   │   │   └── page.tsx          # Progress dashboard
│   │   ├── classroom/            # Teacher features
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   └── layout.tsx            # App shell
│   │
│   ├── api/                      # Minimal - mostly Server Actions
│   │   └── webhooks/
│   │       └── stripe/
│   │           └── route.ts
│   │
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Landing page
│
├── components/
│   ├── launchpad/
│   │   ├── VirtualLaunchpad.tsx  # Main component ⭐
│   │   ├── LaunchpadButton.tsx   # Individual button
│   │   ├── LaunchpadGrid.tsx     # Grid container
│   │   └── ConfigSelector.tsx    # Config picker
│   │
│   ├── audio/
│   │   ├── AudioEngine.tsx       # Web Audio wrapper
│   │   └── useAudio.ts           # Audio hook
│   │
│   ├── lessons/
│   │   ├── LessonPlayer.tsx      # Guided lesson UI
│   │   ├── LessonStep.tsx        # Individual step
│   │   └── ProgressBar.tsx       # Visual progress
│   │
│   ├── ui/                       # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...
│   │
│   └── shared/
│       ├── Header.tsx
│       ├── Footer.tsx
│       └── Navigation.tsx
│
├── lib/
│   ├── supabase/
│   │   ├── client.ts             # Client-side
│   │   ├── server.ts             # Server-side
│   │   └── middleware.ts         # Auth middleware
│   │
│   ├── audio/
│   │   ├── engine.ts             # Audio Engine class
│   │   ├── frequencies.ts        # Note frequency map
│   │   └── synthesis.ts          # Oscillator/envelope logic
│   │
│   ├── config/
│   │   ├── presets.ts            # 5 default configs
│   │   ├── validator.ts          # Config validation
│   │   └── transformer.ts        # YAML ↔ JSON
│   │
│   └── utils/
│       ├── cn.ts                 # className utility
│       └── format.ts             # Date/time formatting
│
├── hooks/
│   ├── useAudioEngine.ts         # Audio context management
│   ├── useConfig.ts              # Config state
│   ├── useProgress.ts            # Lesson progress
│   └── useSupabase.ts            # Supabase client
│
├── types/
│   ├── config.ts                 # ConfigData interface
│   ├── lesson.ts                 # Lesson interfaces
│   └── database.ts               # Supabase types (auto-generated)
│
├── public/
│   ├── sounds/                   # Optional WAV samples
│   ├── icons/                    # App icons
│   └── manifest.json             # PWA manifest
│
├── supabase/
│   ├── migrations/               # Database migrations
│   └── functions/                # Edge functions
│
└── package.json
```

---

## 5. Key Components Deep Dive

### VirtualLaunchpad Component

```typescript
// components/launchpad/VirtualLaunchpad.tsx
'use client'

import { useRef, useEffect, useState } from 'react';
import { useAudioEngine } from '@/hooks/useAudioEngine';
import { LaunchpadButton } from './LaunchpadButton';
import type { ConfigData } from '@/types/config';

interface VirtualLaunchpadProps {
  config: ConfigData;
  onNotePlay?: (note: string, position: [number, number]) => void;
  highlightButton?: { x: number; y: number } | null;
  disabled?: boolean;
}

export function VirtualLaunchpad({
  config,
  onNotePlay,
  highlightButton,
  disabled = false
}: VirtualLaunchpadProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { playNote, stopNote } = useAudioEngine();
  const [activeButtons, setActiveButtons] = useState<Set<string>>(new Set());

  // Grid dimensions (9x9)
  const GRID_SIZE = 9;

  const handleButtonPress = (x: number, y: number) => {
    if (disabled) return;

    const note = config.layout.grid[y][x];
    if (note === 'x') return; // Empty cell

    const buttonKey = `${x}-${y}`;
    setActiveButtons(prev => new Set(prev).add(buttonKey));

    playNote(note, config.audio);
    onNotePlay?.(note, [x, y]);
  };

  const handleButtonRelease = (x: number, y: number) => {
    const note = config.layout.grid[y][x];
    if (note === 'x') return;

    const buttonKey = `${x}-${y}`;
    setActiveButtons(prev => {
      const next = new Set(prev);
      next.delete(buttonKey);
      return next;
    });

    stopNote(note);
  };

  return (
    <div
      ref={containerRef}
      className="aspect-square w-full max-w-2xl mx-auto p-4 bg-gray-900 rounded-2xl"
    >
      <div
        className="grid grid-cols-9 gap-1 h-full"
        style={{ touchAction: 'none' }} // Prevent scroll on touch
      >
        {Array.from({ length: GRID_SIZE }).map((_, y) =>
          Array.from({ length: GRID_SIZE }).map((_, x) => {
            const note = config.layout.grid[y][x];
            const buttonKey = `${x}-${y}`;
            const isActive = activeButtons.has(buttonKey);
            const isHighlighted =
              highlightButton?.x === x && highlightButton?.y === y;

            return (
              <LaunchpadButton
                key={buttonKey}
                x={x}
                y={y}
                note={note}
                color={note !== 'x' ? config.colors[note] : [0, 0, 0]}
                isActive={isActive}
                isHighlighted={isHighlighted}
                onPress={() => handleButtonPress(x, y)}
                onRelease={() => handleButtonRelease(x, y)}
              />
            );
          })
        )}
      </div>
    </div>
  );
}
```

### LaunchpadButton Component

```typescript
// components/launchpad/LaunchpadButton.tsx
'use client'

import { useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface LaunchpadButtonProps {
  x: number;
  y: number;
  note: string;
  color: [number, number, number];
  isActive: boolean;
  isHighlighted: boolean;
  onPress: () => void;
  onRelease: () => void;
}

export function LaunchpadButton({
  note,
  color,
  isActive,
  isHighlighted,
  onPress,
  onRelease
}: LaunchpadButtonProps) {
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Convert RGB to CSS
  const [r, g, b] = color;
  const baseColor = `rgb(${r}, ${g}, ${b})`;
  const activeColor = `rgb(${Math.min(r + 50, 255)}, ${Math.min(g + 50, 255)}, ${Math.min(b + 50, 255)})`;

  // Handle touch events
  useEffect(() => {
    const button = buttonRef.current;
    if (!button) return;

    const handleTouchStart = (e: TouchEvent) => {
      e.preventDefault();
      onPress();
    };

    const handleTouchEnd = (e: TouchEvent) => {
      e.preventDefault();
      onRelease();
    };

    button.addEventListener('touchstart', handleTouchStart);
    button.addEventListener('touchend', handleTouchEnd);
    button.addEventListener('touchcancel', handleTouchEnd);

    return () => {
      button.removeEventListener('touchstart', handleTouchStart);
      button.removeEventListener('touchend', handleTouchEnd);
      button.removeEventListener('touchcancel', handleTouchEnd);
    };
  }, [onPress, onRelease]);

  const isEmpty = note === 'x';

  return (
    <button
      ref={buttonRef}
      className={cn(
        "aspect-square rounded-lg transition-all duration-75",
        "active:scale-95 select-none",
        isEmpty && "opacity-20 cursor-default",
        isHighlighted && "ring-4 ring-white ring-offset-2 ring-offset-gray-900 animate-pulse"
      )}
      style={{
        backgroundColor: isActive ? activeColor : baseColor,
        boxShadow: isActive
          ? `0 0 20px ${baseColor}`
          : `0 2px 4px rgba(0,0,0,0.3)`
      }}
      onMouseDown={onPress}
      onMouseUp={onRelease}
      onMouseLeave={onRelease}
      disabled={isEmpty}
    >
      {/* Optional: Show note name for learning mode */}
      {!isEmpty && (
        <span className="text-white text-xs opacity-0 hover:opacity-100">
          {note}
        </span>
      )}
    </button>
  );
}
```

### Audio Engine Hook

```typescript
// hooks/useAudioEngine.ts
'use client'

import { useRef, useEffect, useCallback } from 'react';
import { AudioEngine } from '@/lib/audio/engine';
import type { AudioConfig } from '@/types/config';

export function useAudioEngine() {
  const engineRef = useRef<AudioEngine | null>(null);

  // Initialize audio context
  useEffect(() => {
    engineRef.current = new AudioEngine();

    return () => {
      engineRef.current?.destroy();
    };
  }, []);

  const playNote = useCallback((note: string, config?: AudioConfig) => {
    engineRef.current?.playNote(note, config);
  }, []);

  const stopNote = useCallback((note: string) => {
    engineRef.current?.stopNote(note);
  }, []);

  const setVolume = useCallback((volume: number) => {
    engineRef.current?.setVolume(volume);
  }, []);

  return {
    playNote,
    stopNote,
    setVolume,
    engine: engineRef.current
  };
}
```

---

## 6. Performance Optimizations

### Bundle Size
```typescript
// Next.js automatic optimizations
{
  "code_splitting": "automatic",
  "tree_shaking": true,
  "minification": true,
  "image_optimization": true,
  "font_optimization": true
}

// Manual optimizations
// 1. Dynamic imports for heavy components
const LessonPlayer = dynamic(() => import('@/components/lessons/LessonPlayer'), {
  loading: () => <LoadingSpinner />
});

// 2. Lazy load audio samples
const loadAudioSample = (url: string) => {
  return import(`@/public/sounds/${url}`);
};
```

### Audio Latency
```typescript
// Minimize latency strategies:
// 1. Preload AudioContext
useEffect(() => {
  const ctx = new AudioContext();
  // Unlock on user interaction (iOS requirement)
  document.addEventListener('touchstart', () => {
    ctx.resume();
  }, { once: true });
}, []);

// 2. Use OscillatorNode (near-zero latency)
// vs <audio> element (50-200ms latency)

// 3. Avoid GC during playback
// Pre-allocate buffers, reuse nodes
```

### Rendering Performance
```typescript
// 1. React.memo for buttons
export const LaunchpadButton = React.memo(Button);

// 2. Virtual scrolling for long lists
import { FixedSizeGrid } from 'react-window';

// 3. Debounce heavy operations
import { useDebouncedCallback } from 'use-debounce';
```

---

## 7. Security

### Authentication Flow
```typescript
// Supabase handles:
// - JWT token generation
// - Refresh token rotation
// - Session persistence (localStorage/cookies)

// We handle:
// - Protected route middleware
// - RLS policies in database
// - Client-side auth state
```

### Row Level Security (RLS) Examples
```sql
-- Users can only update own profile
CREATE POLICY "Users update own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Users can view public configs OR their own
CREATE POLICY "View configs"
  ON configs FOR SELECT
  USING (
    is_public = true
    OR user_id = auth.uid()
    OR EXISTS (
      SELECT 1 FROM classroom_students cs
      JOIN classrooms c ON c.id = cs.classroom_id
      WHERE cs.student_id = auth.uid()
      AND c.teacher_id = configs.user_id
    )
  );
```

### API Security
```typescript
// Server Actions are protected by default
'use server'

export async function deleteConfig(configId: string) {
  const supabase = createServerClient();
  const user = await supabase.auth.getUser();

  if (!user.data.user) {
    return { error: 'Unauthorized' };
  }

  // RLS ensures user can only delete own configs
  const { error } = await supabase
    .from('configs')
    .delete()
    .eq('id', configId);

  return { error };
}
```

---

## 8. Monitoring & Analytics

### Performance Monitoring
```typescript
// Vercel Analytics (built-in)
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}

// Web Vitals tracking
import { SpeedInsights } from '@vercel/speed-insights/next';
```

### User Analytics
```typescript
// PostHog or Plausible (privacy-friendly)
import posthog from 'posthog-js';

// Track events
posthog.capture('note_played', {
  note: 'C',
  config: 'baby_mode',
  session_duration: 120
});

// Track lessons
posthog.capture('lesson_completed', {
  lesson_id: 'lesson-1',
  time_taken: 180,
  score: 100
});
```

---

## 9. Deployment Pipeline

### CI/CD with GitHub Actions + Vercel

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run lint

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run type-check

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run test

# Vercel auto-deploys on push to main
```

### Environment Strategy
```
Development:
  - Local dev server (npm run dev)
  - Local Supabase (docker-compose)
  - Localhost:3000

Preview (per PR):
  - Vercel preview URL
  - Supabase staging project
  - Auto-deployed on PR

Production:
  - babysynth.com
  - Supabase production project
  - Auto-deployed on merge to main
```

---

## 10. Testing Strategy

### Unit Tests (Vitest)
```typescript
// lib/audio/engine.test.ts
import { describe, it, expect } from 'vitest';
import { AudioEngine } from './engine';

describe('AudioEngine', () => {
  it('plays note at correct frequency', () => {
    const engine = new AudioEngine();
    const osc = engine.playNote('C');
    expect(osc.frequency.value).toBe(261.63);
  });
});
```

### Component Tests (React Testing Library)
```typescript
// components/launchpad/VirtualLaunchpad.test.tsx
import { render, fireEvent } from '@testing-library/react';
import { VirtualLaunchpad } from './VirtualLaunchpad';

test('plays note on button click', () => {
  const onNotePlay = vi.fn();
  const { getByRole } = render(
    <VirtualLaunchpad config={mockConfig} onNotePlay={onNotePlay} />
  );

  fireEvent.click(getByRole('button', { name: /C/i }));
  expect(onNotePlay).toHaveBeenCalledWith('C', [0, 0]);
});
```

### E2E Tests (Playwright)
```typescript
// e2e/play.spec.ts
import { test, expect } from '@playwright/test';

test('can play notes on virtual launchpad', async ({ page }) => {
  await page.goto('/play');
  await page.click('[data-testid="launchpad-button-0-0"]');
  await expect(page.locator('.active-note')).toBeVisible();
});
```

---

## 11. Next Steps

### Immediate
- [ ] Initialize Next.js 14 project
- [ ] Set up Supabase project
- [ ] Configure TailwindCSS + shadcn/ui
- [ ] Create basic file structure

### Week 1
- [ ] Build VirtualLaunchpad component
- [ ] Implement AudioEngine
- [ ] Create 5 base configs
- [ ] Set up routing

### Week 2
- [ ] Implement Supabase auth
- [ ] Build marketplace (read-only)
- [ ] Create dashboard
- [ ] Add save/load

### Week 3
- [ ] Build lesson system
- [ ] Create 10 lessons
- [ ] Add progress tracking
- [ ] Polish UI/UX

---

**Status:** Ready to build! ✅

**Next Document:** Development Roadmap
