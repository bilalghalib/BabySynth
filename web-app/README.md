# 🎹 BabySynth Web App

A browser-based virtual Launchpad that makes music education accessible to everyone. No hardware required!

## ✨ What's Built

This is a fully functional MVP featuring:

### Core Features
- **Virtual Launchpad**: Interactive 9x9 grid of colorful LED buttons
- **Real-time Audio Synthesis**: Web Audio API with <50ms latency
- **5 Pre-loaded Configurations**:
  - 👶 Baby Mode - Simple, large buttons, primary colors
  - 🎉 Party Mode - Bright disco colors, energetic sounds
  - 🌙 Bedtime Mode - Soft blues, gentle tones
  - 📚 Learning Mode - Note name education
  - 🥁 Drum Kit - Percussion-focused rhythms

### Technical Highlights
- **Audio Engine** (`src/hooks/useAudioEngine.ts`):
  - Multiple waveforms (sine, square, triangle, sawtooth)
  - ADSR envelope system
  - Polyphonic playback
  - iOS Safari compatibility
- **Touch-responsive** grid works on mobile/tablet/desktop
- **Smooth animations** with Framer Motion
- **TypeScript** for type safety
- **Supabase** integration ready (auth/database)

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000) to see the app.

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Home page with Virtual Launchpad
│   └── layout.tsx         # Root layout
├── components/
│   └── launchpad/         # Launchpad components
│       ├── VirtualLaunchpad.tsx   # Main grid component
│       └── LaunchpadButton.tsx    # Individual button
├── configs/               # Pre-loaded configurations
│   ├── baby.ts
│   ├── party.ts
│   ├── bedtime.ts
│   ├── learning.ts
│   └── drums.ts
├── hooks/
│   └── useAudioEngine.ts  # Web Audio API synthesis
├── lib/
│   ├── supabase/          # Supabase client setup
│   └── utils.ts           # Utility functions
└── types/
    └── index.ts           # TypeScript types
```

## 🎨 Creating Custom Configurations

Configurations are TypeScript objects. Example:

```typescript
import type { LaunchpadConfig } from '@/types'

export const myConfig: LaunchpadConfig = {
  name: 'My Config',
  description: 'Custom sounds',
  layout: {
    grid: [
      // 9x9 array of note names
      ['C', 'D', 'E', 'F', 'G', 'A', 'B', 'C', 'x'],
      // ... 8 more rows
    ],
    scale: ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
  },
  colors: {
    'C': [255, 0, 0],  // RGB
    'D': [0, 255, 0],
    // ... more notes
  },
  audio: {
    waveform: 'sine',
    envelope: {
      attack: 0.1,
      decay: 0.2,
      sustain: 0.7,
      release: 0.3,
    },
  },
}
```

Add to `src/configs/index.ts` to include in the config selector.

## 📚 Documentation

See the `docs/` directory for comprehensive documentation:

- **[PRD.md](docs/PRD.md)** - Product requirements and MVP features
- **[TECHNICAL_ARCHITECTURE.md](docs/TECHNICAL_ARCHITECTURE.md)** - System architecture
- **[ROADMAP.md](docs/ROADMAP.md)** - 3-week development roadmap
- **[DATABASE_SCHEMA.sql](docs/DATABASE_SCHEMA.sql)** - Supabase schema

## 🎯 Next Steps

According to the roadmap, Week 2 priorities are:

1. **User Authentication** (Supabase Auth)
   - Email + password signup
   - Google OAuth
   - Session management

2. **Config Marketplace**
   - Browse community configs
   - Like/favorite configs
   - Share links

3. **Parent Dashboard**
   - Play time tracking
   - Recently played configs
   - Basic analytics

See `docs/ROADMAP.md` for detailed day-by-day tasks.

## 🔧 Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **Animation**: Framer Motion
- **Audio**: Web Audio API
- **Backend**: Supabase (ready to configure)
- **Deployment**: Vercel (recommended)

## 🌐 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Other Platforms

The app is a standard Next.js application and can be deployed to:
- Netlify
- Railway
- AWS Amplify
- Any Node.js hosting

## 🎵 Audio Notes

- **iOS Safari**: Audio requires user interaction to unlock. The app prompts users to tap.
- **Latency**: Optimized for <50ms latency on modern browsers
- **Polyphony**: Multiple notes can play simultaneously
- **Waveforms**: Supports sine, square, triangle, sawtooth

## 📝 License

Part of the BabySynth project. See root README for details.

## 🤝 Contributing

This implements Week 1 deliverables from the development roadmap. See `docs/ROADMAP.md` for upcoming features.

---

**Status**: ✅ Week 1 MVP Complete
**Next**: Week 2 - User Accounts & Social Features
