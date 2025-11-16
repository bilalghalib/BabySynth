# BabySynth Web - Development Roadmap

**Timeline:** 3 weeks to MVP
**Launch Date:** Week 4
**Team Size:** 1 developer (Claude-assisted)

---

## Overview

```
Week 1: Core Experience
Week 2: User Accounts & Social
Week 3: Educational Features
Week 4: Polish & Launch
```

---

## Week 1: Core Experience (Nov 16-22)

### Goal
**Ship a working virtual Launchpad that makes sounds**

### Success Criteria
- ✅ Can tap/click grid and hear notes
- ✅ Works on iPad Safari
- ✅ Audio latency <100ms
- ✅ 5 pre-loaded configs switchable
- ✅ Mobile responsive
- ✅ No critical bugs

---

### Day 1 (Monday): Project Setup
**Time:** 4 hours

**Tasks:**
- [ ] Create Next.js 14 project
  ```bash
  npx create-next-app@latest babysynth-web --typescript --tailwind --app
  ```
- [ ] Configure TypeScript strict mode
- [ ] Set up Supabase project (free tier)
- [ ] Install dependencies:
  ```bash
  npm install @supabase/supabase-js
  npm install class-variance-authority clsx tailwind-merge
  npm install lucide-react framer-motion
  ```
- [ ] Set up shadcn/ui
  ```bash
  npx shadcn-ui@latest init
  npx shadcn-ui@latest add button card dialog
  ```
- [ ] Create folder structure (see TECHNICAL_ARCHITECTURE.md)
- [ ] Configure environment variables

**Deliverable:** Empty app runs locally ✅

---

### Day 2 (Tuesday): Audio Engine
**Time:** 6 hours

**Tasks:**
- [ ] Create AudioEngine class (`lib/audio/engine.ts`)
  - [ ] AudioContext initialization
  - [ ] Note frequency map (C=261.63Hz, etc.)
  - [ ] OscillatorNode creation
  - [ ] GainNode for volume
  - [ ] Basic ADSR envelope
- [ ] Create useAudioEngine hook
- [ ] Test audio on iOS Safari (unlock context)
- [ ] Handle multiple simultaneous notes (polyphony)
- [ ] Add volume control
- [ ] Write unit tests

**Deliverable:** Audio plays when function called ✅

**Code Snippets:**
```typescript
// lib/audio/engine.ts
export class AudioEngine {
  private audioContext: AudioContext;
  private masterGain: GainNode;
  private activeNotes: Map<string, { osc: OscillatorNode; gain: GainNode }>;

  constructor() {
    this.audioContext = new AudioContext();
    this.masterGain = this.audioContext.createGain();
    this.masterGain.connect(this.audioContext.destination);
    this.activeNotes = new Map();
  }

  playNote(note: string, config?: AudioConfig) {
    const freq = this.getFrequency(note);
    const osc = this.audioContext.createOscillator();
    const gain = this.audioContext.createGain();

    osc.type = config?.waveform || 'sine';
    osc.frequency.value = freq;

    gain.connect(this.masterGain);
    osc.connect(gain);

    // ADSR envelope
    const now = this.audioContext.currentTime;
    const { attack, decay, sustain } = config?.envelope || DEFAULT_ENVELOPE;

    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(1, now + attack);
    gain.gain.linearRampToValueAtTime(sustain, now + attack + decay);

    osc.start();
    this.activeNotes.set(note, { osc, gain });
  }

  stopNote(note: string) {
    const noteData = this.activeNotes.get(note);
    if (!noteData) return;

    const { osc, gain } = noteData;
    const now = this.audioContext.currentTime;
    const release = 0.3;

    gain.gain.cancelScheduledValues(now);
    gain.gain.setValueAtTime(gain.gain.value, now);
    gain.gain.linearRampToValueAtTime(0, now + release);

    osc.stop(now + release);
    this.activeNotes.delete(note);
  }
}
```

---

### Day 3 (Wednesday): LaunchpadButton Component
**Time:** 5 hours

**Tasks:**
- [ ] Create LaunchpadButton component
  - [ ] Props: x, y, note, color, onPress, onRelease
  - [ ] Touch event handling (prevent scroll)
  - [ ] Mouse event handling
  - [ ] Visual feedback (brightness change on press)
  - [ ] Highlight state (for lessons)
  - [ ] Disabled state
- [ ] Responsive sizing (fills container)
- [ ] Smooth animations (CSS transitions)
- [ ] Test on iOS and Android
- [ ] Storybook stories (optional)

**Deliverable:** Individual button works perfectly ✅

---

### Day 4 (Thursday): VirtualLaunchpad Grid
**Time:** 6 hours

**Tasks:**
- [ ] Create VirtualLaunchpad component
  - [ ] Render 9x9 grid
  - [ ] Connect to AudioEngine
  - [ ] Handle config prop
  - [ ] Map grid positions to notes
  - [ ] Track active buttons (pressed state)
  - [ ] Prevent multi-touch issues
- [ ] Create ConfigSelector component
  - [ ] Dropdown or card grid
  - [ ] Switch configs instantly
  - [ ] Persist to localStorage
- [ ] Create 5 preset configs
  - [ ] Baby Mode
  - [ ] Party Mode
  - [ ] Bedtime Mode
  - [ ] Learning Mode
  - [ ] Drum Kit
- [ ] Optimize rendering (React.memo)

**Deliverable:** Full playable Launchpad ✅

---

### Day 5 (Friday): Page Layout & PWA
**Time:** 5 hours

**Tasks:**
- [ ] Create /play page
  - [ ] Full-screen layout
  - [ ] Config selector at top
  - [ ] VirtualLaunchpad centered
  - [ ] Volume slider
  - [ ] Fullscreen button
- [ ] Create landing page (/)
  - [ ] Hero section with demo video
  - [ ] "Try Free Now" CTA
  - [ ] Features list
  - [ ] Testimonials (mock for now)
- [ ] PWA configuration
  - [ ] manifest.json
  - [ ] Service worker (offline)
  - [ ] App icons (generate with realfavicongenerator.net)
  - [ ] Splash screens
- [ ] Test "Add to Home Screen"
- [ ] Mobile optimization

**Deliverable:** Shippable V0.1 ✅

**Weekend:** Internal testing, fix bugs

---

## Week 2: User Accounts & Social (Nov 23-29)

### Goal
**Users can save configs and browse marketplace**

### Success Criteria
- ✅ Users can sign up/login
- ✅ Configs saved to cloud
- ✅ Marketplace browsable
- ✅ Share links work
- ✅ Dashboard shows activity

---

### Day 6 (Monday): Supabase Auth Setup
**Time:** 4 hours

**Tasks:**
- [ ] Configure Supabase Auth
  - [ ] Enable email/password
  - [ ] Enable Google OAuth
  - [ ] Configure redirect URLs
  - [ ] Set up email templates
- [ ] Create auth middleware
- [ ] Create login page
- [ ] Create signup page
- [ ] Create protected route wrapper
- [ ] Test auth flow

**Deliverable:** Working authentication ✅

---

### Day 7 (Tuesday): Database Schema & RLS
**Time:** 5 hours

**Tasks:**
- [ ] Create database tables
  - [ ] profiles
  - [ ] configs
  - [ ] config_likes
  - [ ] play_sessions
- [ ] Write SQL migrations
- [ ] Set up Row Level Security policies
- [ ] Create database types (generate from Supabase)
- [ ] Write Server Actions for CRUD
  - [ ] saveConfig
  - [ ] loadConfig
  - [ ] deleteConfig
  - [ ] likeConfig
- [ ] Test RLS policies

**Deliverable:** Database ready ✅

---

### Day 8 (Wednesday): Save/Load Configs
**Time:** 6 hours

**Tasks:**
- [ ] Create "Save Config" dialog
  - [ ] Name field
  - [ ] Description textarea
  - [ ] Public/private toggle
  - [ ] Tags (optional)
- [ ] Create "My Configs" page
  - [ ] List user's configs
  - [ ] Load on click
  - [ ] Edit/delete actions
  - [ ] Search/filter
- [ ] Implement save logic (Server Action)
- [ ] Implement load logic
- [ ] Handle conflicts (overwrite prompt)
- [ ] Test thoroughly

**Deliverable:** Cloud save/load works ✅

---

### Day 9 (Thursday): Config Marketplace
**Time:** 6 hours

**Tasks:**
- [ ] Create /marketplace page
  - [ ] Grid layout (cards)
  - [ ] Filters: Trending, New, Top Rated
  - [ ] Search bar
  - [ ] Infinite scroll (pagination)
- [ ] Create ConfigCard component
  - [ ] Thumbnail (grid visualization)
  - [ ] Name, description, author
  - [ ] Like count, download count
  - [ ] "Load" button
  - [ ] "Like" button
- [ ] Create /marketplace/[id] detail page
  - [ ] Full config preview
  - [ ] Author info
  - [ ] Comments section (future)
  - [ ] "Load" and "Fork" buttons
- [ ] Implement like functionality
- [ ] Share URL generation

**Deliverable:** Browsable marketplace ✅

---

### Day 10 (Friday): Dashboard & Analytics
**Time:** 5 hours

**Tasks:**
- [ ] Create /dashboard page
  - [ ] Play time stats (this week, all time)
  - [ ] Recent activity feed
  - [ ] Favorite configs
  - [ ] Quick actions (create, browse)
- [ ] Implement play session tracking
  - [ ] Start session on load
  - [ ] Track duration
  - [ ] Track notes played
  - [ ] End session on unload
- [ ] Create charts (Recharts)
  - [ ] Play time over last 7 days
  - [ ] Most played configs
  - [ ] Notes played distribution
- [ ] Profile settings page
  - [ ] Display name
  - [ ] Avatar upload
  - [ ] Email settings
  - [ ] Delete account

**Deliverable:** Full dashboard ✅

**Weekend:** Testing, bug fixes, polish

---

## Week 3: Educational Features (Nov 30 - Dec 6)

### Goal
**Launch with 10 guided lessons and progress tracking**

### Success Criteria
- ✅ 10 lessons playable
- ✅ Clear instructions
- ✅ Visual highlighting works
- ✅ Success/failure feedback
- ✅ Progress persists
- ✅ Parents see child's progress

---

### Day 11 (Monday): Lesson Data Structure
**Time:** 4 hours

**Tasks:**
- [ ] Design lesson JSON schema
- [ ] Create lessons table in Supabase
- [ ] Create user_progress table
- [ ] Write 10 lesson outlines
  1. Find Middle C
  2. Play a Scale
  3. High vs Low
  4. Colors and Sounds
  5. Copy the Pattern
  6. Make a Melody
  7. Fast vs Slow
  8. Loud vs Quiet
  9. Twinkle Twinkle
  10. Free Composition
- [ ] Insert lessons into database
- [ ] Create types for lessons

**Deliverable:** Lesson data ready ✅

---

### Day 12 (Tuesday): LessonPlayer Component
**Time:** 6 hours

**Tasks:**
- [ ] Create LessonPlayer component
  - [ ] Load lesson data
  - [ ] Display current step
  - [ ] Show instructions
  - [ ] Highlight button to press
  - [ ] Validate user input
  - [ ] Show success/try-again feedback
  - [ ] Progress bar
  - [ ] Next/skip buttons
- [ ] Create LessonStep component
- [ ] Handle lesson completion
  - [ ] Confetti animation
  - [ ] Save to user_progress
  - [ ] Unlock next lesson
  - [ ] Redirect to next or dashboard

**Deliverable:** One lesson playable ✅

---

### Day 13 (Wednesday): All 10 Lessons
**Time:** 6 hours

**Tasks:**
- [ ] Write detailed instructions for each lesson
- [ ] Create custom configs for each (if needed)
- [ ] Test each lesson end-to-end
- [ ] Add difficulty indicators
- [ ] Add estimated time
- [ ] Add tooltips/hints
- [ ] Handle edge cases (user skips steps)
- [ ] Polish animations and transitions

**Deliverable:** 10 polished lessons ✅

---

### Day 14 (Thursday): Progress Tracking & Gamification
**Time:** 6 hours

**Tasks:**
- [ ] Create /lessons page
  - [ ] List all lessons
  - [ ] Show completion status
  - [ ] Lock system (unlock after completing previous)
  - [ ] Stats: X/10 completed
- [ ] Add achievements/badges
  - [ ] "First Lesson Complete"
  - [ ] "5 Lessons Complete"
  - [ ] "All Lessons Complete"
  - [ ] "Played 100 notes"
  - [ ] "Created first config"
- [ ] Add progress to dashboard
  - [ ] "Next lesson: X"
  - [ ] "You're Y% done!"
  - [ ] Encourage to continue
- [ ] Add streaks (days played in a row)
- [ ] Add XP/points system (optional)

**Deliverable:** Engaging progression ✅

---

### Day 15 (Friday): Parent Dashboard & Sharing
**Time:** 5 hours

**Tasks:**
- [ ] Enhance dashboard for parents
  - [ ] Weekly email digest (setup)
  - [ ] Progress report (printable)
  - [ ] Share achievements (social)
- [ ] Create share functionality
  - [ ] "Share my progress" button
  - [ ] Generate shareable image
  - [ ] Copy link to clipboard
  - [ ] Social meta tags (Twitter, FB)
- [ ] Add parent tips
  - [ ] "How to encourage practice"
  - [ ] "What's next in music education"
- [ ] Test entire flow as a parent

**Deliverable:** Parent-friendly features ✅

**Weekend:** Final testing, prepare for launch

---

## Week 4: Polish & Launch (Dec 7-13)

### Goal
**Ship to 100 beta users and collect feedback**

### Success Criteria
- ✅ No critical bugs
- ✅ Performance optimized
- ✅ SEO ready
- ✅ 100 beta signups
- ✅ 10+ testimonials collected

---

### Day 16 (Monday): Bug Bash & Performance
**Time:** 6 hours

**Tasks:**
- [ ] Fix all known bugs
- [ ] Lighthouse audit (aim for 90+ all metrics)
- [ ] Optimize bundle size
  - [ ] Check with `npm run analyze`
  - [ ] Remove unused dependencies
  - [ ] Lazy load heavy components
- [ ] Optimize images (WebP, proper sizing)
- [ ] Add loading states everywhere
- [ ] Add error boundaries
- [ ] Test on slow 3G network
- [ ] Test on various devices

**Deliverable:** Polished app ✅

---

### Day 17 (Tuesday): SEO & Marketing Pages
**Time:** 5 hours

**Tasks:**
- [ ] Landing page polish
  - [ ] Hero section copy
  - [ ] Demo video (30 sec)
  - [ ] Social proof (fake testimonials)
  - [ ] FAQ section
  - [ ] Pricing table (future)
- [ ] Create /about page
- [ ] Create /privacy page
- [ ] Create /terms page
- [ ] Add meta tags (title, description, OG)
- [ ] Add JSON-LD structured data
- [ ] Submit to Google Search Console
- [ ] Create sitemap.xml
- [ ] Add robots.txt

**Deliverable:** SEO ready ✅

---

### Day 18 (Wednesday): Beta Launch Prep
**Time:** 5 hours

**Tasks:**
- [ ] Set up analytics
  - [ ] Vercel Analytics
  - [ ] PostHog or Plausible
  - [ ] Event tracking (critical paths)
- [ ] Set up error tracking (Sentry)
- [ ] Create beta signup form
- [ ] Prepare launch email (for beta users)
- [ ] Create Product Hunt draft
- [ ] Prepare Reddit posts
- [ ] Prepare Twitter thread
- [ ] Record demo video
- [ ] Take screenshots
- [ ] Write press release

**Deliverable:** Launch materials ready ✅

---

### Day 19 (Thursday): Private Beta Launch
**Time:** Full day

**Tasks:**
- [ ] Invite 20 hand-picked beta users
  - [ ] 10 parents
  - [ ] 5 music teachers
  - [ ] 5 friends/family
- [ ] Monitor analytics live
- [ ] Be available for support (Discord/email)
- [ ] Collect feedback via Google Form
- [ ] Watch session recordings (FullStory)
- [ ] Fix critical bugs immediately
- [ ] Iterate based on feedback

**Deliverable:** 20 active beta users ✅

---

### Day 20 (Friday): Iteration & Public Launch
**Time:** Full day

**Tasks:**
- [ ] Implement critical feedback
- [ ] Final bug fixes
- [ ] Public launch:
  - [ ] Post on Product Hunt (aim for top 5)
  - [ ] Post on Reddit (r/parenting, r/musictheory)
  - [ ] Tweet launch thread
  - [ ] Email beta users (ask for upvotes)
  - [ ] Post in Facebook groups
- [ ] Monitor metrics
  - [ ] Signups
  - [ ] Retention
  - [ ] Session duration
  - [ ] Errors
- [ ] Respond to comments/feedback
- [ ] Celebrate! 🎉

**Deliverable:** Public launch ✅

**Goal:** 100 signups in first 24 hours

---

## Post-Launch (Week 5+)

### Immediate Next Steps
- [ ] Collect user testimonials
- [ ] Create case studies (parents + teachers)
- [ ] Fix reported bugs
- [ ] Implement most-requested features
- [ ] A/B test signup flow
- [ ] Optimize conversion funnel

### Month 2 Features
- [ ] Hardware desktop bridge
- [ ] Payment integration (Stripe)
- [ ] Classroom dashboard (teacher features)
- [ ] Config editor (in-browser)
- [ ] Advanced lessons (11-30)
- [ ] Social features (comments, follows)

### Month 3 Features
- [ ] Mobile apps (React Native)
- [ ] MIDI export
- [ ] Video lessons
- [ ] Teacher marketplace
- [ ] White-label for schools
- [ ] API for developers

---

## Success Metrics by Week

### Week 1
- ✅ Launchpad playable
- ✅ 0 critical bugs
- ✅ Works on iOS

### Week 2
- ✅ Auth functional
- ✅ Configs save/load
- ✅ Marketplace browsable

### Week 3
- ✅ 10 lessons complete
- ✅ Progress tracked
- ✅ Dashboard useful

### Week 4
- ✅ 100 signups
- ✅ 30% D1 retention
- ✅ 10+ testimonials
- ✅ Product Hunt launch

### Month 1
- 🎯 1,000 users
- 🎯 50 paid subscribers
- 🎯 $500 MRR
- 🎯 10 schools interested

---

## Risk Mitigation

### Risk: Audio doesn't work on iOS
**Mitigation:**
- Test early (Day 2)
- Use Web Audio API best practices
- Have fallback plan (pre-recorded samples)

### Risk: Timeline slips
**Mitigation:**
- MVP scope is minimal
- Can cut features (marketplace can be read-only)
- Claude helps with code velocity

### Risk: No user interest
**Mitigation:**
- Validate with beta users
- Pivot based on feedback
- Have backup marketing channels

---

## Daily Standup Questions

**What did I ship yesterday?**
**What am I shipping today?**
**What's blocking me?**

---

## Definition of Done

A feature is "done" when:
- [ ] Code written and tested
- [ ] Works on mobile and desktop
- [ ] No console errors
- [ ] Accessible (keyboard nav, screen readers)
- [ ] Responsive design
- [ ] Loading states added
- [ ] Error handling implemented
- [ ] Deployed to preview URL
- [ ] Reviewed (self or peer)
- [ ] Documented (if needed)

---

**Let's build! 🚀**

**Status:** Ready to start coding ✅
**Next:** Create database schema and start building!
