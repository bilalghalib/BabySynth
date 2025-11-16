# BabySynth Web MVP - Product Requirements Document (PRD)

**Version:** 1.0
**Date:** 2025-11-16
**Status:** Planning
**Owner:** Product Team

---

## 1. Executive Summary

### Vision
Transform BabySynth from a hardware-only music toy into a hybrid web/hardware platform that makes music education accessible to every child with a tablet, while maintaining premium hardware integration for serious users.

### Mission
Launch a freemium web app that:
- Generates 10,000 users in 3 months
- Converts 5% to paid ($500 MRR)
- Validates classroom market (10 pilot schools)
- Creates viral growth through sharing

### Success Metrics
```
Month 1: 1,000 users, 50 paid, $500 MRR
Month 2: 3,000 users, 120 paid, $1,200 MRR
Month 3: 10,000 users, 500 paid, $5,000 MRR
```

---

## 2. Problem Statement

### Current State
- BabySynth is Python-only
- Requires $200 Launchpad hardware
- Addressable market: ~100K Launchpad owners
- No way to try before buying
- Can't go viral
- Can't sell to schools (budget constraints)

### Target Users

#### Primary: Parents (0-4 year olds)
**Demographics:**
- Age: 25-40
- Income: $60K+
- Education: College+
- Tech-savvy, values early learning

**Pain Points:**
- Too much screen time concerns
- Want educational toys
- Expensive music lessons ($100+/month)
- Don't know if baby likes music yet
- Need activity ideas

**Jobs to Be Done:**
- Introduce baby to music
- Reduce screen time with interactive play
- Prepare for music lessons
- Entertain during fussy moments
- Share activities with caregivers/grandparents

#### Secondary: Music Teachers (K-5)
**Demographics:**
- Age: 25-55
- 30-40% use tech in classroom
- Limited budget ($500-2000/year for supplies)
- 20-30 students per class

**Pain Points:**
- Need engaging digital tools
- Must work on existing tablets
- No time to learn complex software
- Need progress tracking for parents
- Limited music equipment budget

**Jobs to Be Done:**
- Teach note names/reading
- Engage students with technology
- Track individual progress
- Justify program value to admin
- Differentiate instruction

#### Tertiary: Music Therapists
**Demographics:**
- Clinical settings
- Work with special needs children
- Need customizable tools
- Budget for equipment

---

## 3. Solution Overview

### Product Description
A web-based virtual Launchpad that works in any browser, featuring:
- Touch-responsive 9x9 grid
- Real-time audio synthesis
- Cloud-saved configurations
- Guided music lessons
- Community-created content
- Optional hardware integration (premium)

### Core Value Propositions

**For Parents:**
- "Try BabySynth free before buying hardware"
- "No installation, works on your iPad"
- "Share your baby's creations with grandma"
- "Track musical development"

**For Teachers:**
- "Music education on the tablets you already have"
- "30 students, one dashboard"
- "Standards-aligned curriculum included"
- "$29/month vs $6000 for instruments"

**For Therapists:**
- "Fully customizable for each client"
- "Clinical-grade progress tracking"
- "Works with existing equipment"

---

## 4. MVP Feature Set (3-Week Timeline)

### Phase 1: Core Experience (Week 1)

#### F1.1 Virtual Launchpad Grid
**Priority:** P0 (Critical)
**User Story:** As a parent, I want to tap colorful buttons that make sounds, so my baby is entertained and learns cause-effect.

**Acceptance Criteria:**
- [ ] 9x9 grid renders on screen
- [ ] Each button shows color (from config)
- [ ] Tap plays note immediately (<50ms latency)
- [ ] Visual feedback on press (brightness change)
- [ ] Works on mobile/tablet (touch)
- [ ] Works on desktop (mouse)
- [ ] Responsive layout (fills screen)

**Technical Requirements:**
- HTML5 Canvas for grid rendering
- Web Audio API for synthesis
- Touch event handling
- 60fps animation

---

#### F1.2 Audio Synthesis Engine
**Priority:** P0 (Critical)
**User Story:** As a user, I want to hear pleasant musical notes when I press buttons.

**Acceptance Criteria:**
- [ ] Sine wave generation per note
- [ ] Correct frequencies (C=261.63Hz, etc.)
- [ ] Multiple simultaneous notes (polyphony)
- [ ] Smooth attack/release (no clicks)
- [ ] Volume control
- [ ] Works on iOS Safari (unlock audio context)

**Technical Requirements:**
- Web Audio API OscillatorNode
- ADSR envelope (basic)
- GainNode for volume
- Audio context management

---

#### F1.3 Pre-loaded Configurations
**Priority:** P0 (Critical)
**User Story:** As a new user, I want ready-to-use setups so I can start immediately.

**Acceptance Criteria:**
- [ ] 5 configs included: Baby, Party, Bedtime, Learning, Drums
- [ ] Switch configs instantly
- [ ] Each has unique colors/layout
- [ ] Config picker UI (dropdown or cards)
- [ ] Persist last-used config (localStorage)

**Configs:**
```
1. Baby Mode - Simple, large buttons, primary colors
2. Party Mode - Bright, disco colors, upbeat
3. Bedtime Mode - Soft blues, gentle sounds
4. Learning Mode - Labeled notes (C, D, E...)
5. Drum Kit - Percussion sounds, rhythm focus
```

---

#### F1.4 Mobile PWA
**Priority:** P1 (High)
**User Story:** As a parent, I want to install the app on my iPad so it feels like a native app.

**Acceptance Criteria:**
- [ ] PWA manifest.json
- [ ] Service worker for offline
- [ ] "Add to Home Screen" prompt
- [ ] Full-screen mode
- [ ] App icon
- [ ] Splash screen

---

### Phase 2: User Accounts & Saving (Week 2)

#### F2.1 User Authentication
**Priority:** P0 (Critical)
**User Story:** As a user, I want to create an account so I can save my progress.

**Acceptance Criteria:**
- [ ] Email + password signup
- [ ] Google OAuth login
- [ ] Email verification
- [ ] Password reset
- [ ] Session persistence
- [ ] Profile page (basic)

**Technical Requirements:**
- Supabase Auth
- Protected routes
- Auth state management

---

#### F2.2 Config Marketplace (Read-Only)
**Priority:** P1 (High)
**User Story:** As a user, I want to browse community configs so I can find new sounds.

**Acceptance Criteria:**
- [ ] Browse page with grid/list view
- [ ] Filter: Trending, New, Top Rated
- [ ] Preview config (thumbnail/animation)
- [ ] One-click load
- [ ] Like/favorite configs
- [ ] Share link to config

**Database Schema:**
```sql
configs:
  - id (uuid)
  - user_id (fk)
  - name (text)
  - description (text)
  - config_data (jsonb)
  - is_public (bool)
  - likes_count (int)
  - downloads_count (int)
  - created_at (timestamp)
```

---

#### F2.3 Save Custom Configs
**Priority:** P1 (High)
**User Story:** As a pro user, I want to save my custom configs to the cloud.

**Acceptance Criteria:**
- [ ] "Save Config" button
- [ ] Name + description fields
- [ ] Save to user account
- [ ] Load from "My Configs" page
- [ ] Edit existing configs
- [ ] Delete configs
- [ ] Make public/private toggle

---

### Phase 3: Educational Core (Week 3)

#### F3.1 Guided Lessons
**Priority:** P0 (Critical)
**User Story:** As a parent, I want structured lessons so my child learns music basics.

**Acceptance Criteria:**
- [ ] 10 lessons included
- [ ] Step-by-step instructions
- [ ] Highlight which button to press
- [ ] Success/try-again feedback
- [ ] Progress tracking
- [ ] Unlock system (complete to unlock next)

**Lesson Topics:**
1. Find Middle C
2. Play a Scale (C Major)
3. High vs Low Notes
4. Colors and Sounds
5. Copy the Pattern
6. Make a Melody
7. Fast vs Slow
8. Loud vs Quiet
9. Your First Song (Twinkle Twinkle)
10. Free Composition

---

#### F3.2 Parent Dashboard
**Priority:** P1 (High)
**User Story:** As a parent, I want to see my child's progress so I can encourage learning.

**Acceptance Criteria:**
- [ ] Total play time (this week, all time)
- [ ] Lessons completed list
- [ ] Recently played configs
- [ ] Achievements/badges
- [ ] Activity chart (time spent per day)
- [ ] Share progress (screenshot/link)

**Database Schema:**
```sql
user_progress:
  - user_id (fk)
  - lesson_id (fk)
  - completed_at (timestamp)
  - score (int)
  - time_spent (int seconds)

play_sessions:
  - user_id (fk)
  - config_id (fk)
  - started_at (timestamp)
  - ended_at (timestamp)
  - notes_played (int)
```

---

#### F3.3 Simple Config Editor
**Priority:** P2 (Nice-to-have)
**User Story:** As an advanced user, I want to create custom configs in the browser.

**Acceptance Criteria:**
- [ ] Visual grid painter
- [ ] Color picker per note
- [ ] Save to account
- [ ] Preview mode
- [ ] Fork existing configs
- [ ] Export as JSON

---

## 5. Non-Goals (Out of Scope for MVP)

❌ **Not Building:**
- Recording/MIDI export
- Advanced audio effects (reverb, delay)
- Multi-user real-time collaboration
- Video lessons
- Teacher dashboard (defer to Month 2)
- Hardware bridge (defer to Month 2)
- Payment processing (defer until validation)
- Mobile apps (iOS/Android native)
- Animation editor (use pre-built animations)
- Social features (comments, follows)

---

## 6. User Flows

### Flow 1: First-Time User (Free)
```
1. Land on homepage
2. See demo video (30 sec)
3. Click "Try Free Now"
4. Virtual Launchpad loads (Baby Mode)
5. Tap buttons, hear sounds
6. Prompt: "Sign up to save progress"
7. Create account (email or Google)
8. Tutorial lesson starts
9. Complete first lesson
10. Unlock more lessons
```

### Flow 2: Returning User
```
1. Visit app
2. Auto-login (session)
3. Last config loads automatically
4. Continue playing
5. Check dashboard for progress
6. Browse marketplace
7. Load new config
8. Share with friend
```

### Flow 3: Teacher Evaluation
```
1. Teacher lands on homepage
2. Clicks "For Educators"
3. Watches classroom demo video
4. Starts free trial (30 days)
5. Creates class (25 students)
6. Students join via code
7. Teacher assigns Lesson 1
8. Watches student progress live
9. Reviews class analytics
10. Decides to purchase
```

---

## 7. Monetization (Future - Post-MVP)

### Free Tier (Always Free)
- ✅ Virtual Launchpad
- ✅ 5 pre-loaded configs
- ✅ Browse marketplace (view only)
- ✅ First 5 lessons
- ✅ 30 min/day play limit
- ❌ No saving custom configs
- ❌ No progress tracking

### Pro Tier ($9.99/month or $99/year)
- ✅ Unlimited play time
- ✅ Save unlimited configs
- ✅ Full lesson library (50+ lessons)
- ✅ Progress dashboard
- ✅ Download configs offline
- ✅ No ads
- ✅ Hardware bridge (when released)
- ✅ Priority support

### Classroom Tier ($29.99/month)
- ✅ Everything in Pro
- ✅ Up to 30 student accounts
- ✅ Teacher dashboard
- ✅ Class management tools
- ✅ Standards-aligned curriculum
- ✅ Reporting/analytics
- ✅ Parent communication tools

---

## 8. Success Criteria

### Must-Have (Launch Blockers)
- [ ] Virtual Launchpad works on iPad Safari
- [ ] <100ms audio latency
- [ ] 5 configs included
- [ ] User accounts functional
- [ ] 10 lessons complete
- [ ] Mobile responsive
- [ ] No crashes/bugs in core flow

### Should-Have (Launch with caveats OK)
- [ ] Config marketplace (read-only OK)
- [ ] Parent dashboard (basic stats OK)
- [ ] PWA installable
- [ ] Smooth 60fps animations

### Nice-to-Have (Can ship later)
- [ ] Config editor
- [ ] Social sharing
- [ ] Advanced lessons
- [ ] Teacher features

---

## 9. Launch Metrics

### Week 1 Goals
- 100 signups
- 50 DAU
- 10 min avg session
- 0 critical bugs

### Week 2 Goals
- 300 signups
- 120 DAU
- 5 lessons completed (avg)
- 20% D1 retention

### Week 3 Goals
- 1,000 signups
- 300 DAU
- 10 configs saved (total)
- 30% D7 retention

### Month 1 Success = Product-Market Fit Signals
- ✅ 1,000+ users
- ✅ 30%+ D7 retention
- ✅ 20+ min avg session
- ✅ 50+ organic shares
- ✅ 5+ teachers request classroom features
- ✅ Positive user feedback (NPS >30)

---

## 10. Risks & Mitigations

### Risk 1: Audio Latency on Mobile
**Impact:** High - Core experience breaks
**Probability:** Medium
**Mitigation:**
- Test on real iOS devices early
- Use Web Audio API best practices
- Preload audio contexts
- Fallback to simple synth if needed

### Risk 2: No Viral Growth
**Impact:** High - Can't reach user goals
**Probability:** Medium
**Mitigation:**
- Built-in sharing (each config = shareable link)
- Referral system (invite friends)
- Social proof (X configs created today)
- Teacher/parent testimonials

### Risk 3: Free Users Don't Convert
**Impact:** Medium - Revenue goals missed
**Probability:** Medium
**Mitigation:**
- Clear upgrade prompts
- Limit free tier meaningfully
- Show value of paid features
- Trial period for premium

### Risk 4: Tech Stack Learning Curve
**Impact:** Medium - Timeline slips
**Probability:** Low
**Mitigation:**
- Use familiar tech (React)
- Reference existing Supabase examples
- Claude can help with code
- MVP scoped tightly

---

## 11. Open Questions

1. **Audio format:** Web Audio synth vs pre-recorded samples?
   - **Decision:** Start with Web Audio (smaller, more flexible)

2. **Freemium limit:** 30 min/day or 5 sessions/day?
   - **Decision:** TBD - test both in beta

3. **Lesson format:** Interactive vs video?
   - **Decision:** Interactive (higher engagement)

4. **Marketplace:** Allow sales or free only?
   - **Decision:** Free only for MVP (avoid payment complexity)

5. **Hardware bridge:** Build now or later?
   - **Decision:** Later (Month 2) - validate web-only first

---

## 12. Next Steps

### Immediate (This Week)
- [x] Write PRD (this document)
- [ ] Create technical architecture doc
- [ ] Design database schema
- [ ] Create mockups/wireframes
- [ ] Set up Next.js project
- [ ] Configure Supabase

### Week 1 Sprint
- [ ] Build virtual Launchpad component
- [ ] Implement audio engine
- [ ] Create 5 base configs
- [ ] Basic routing/navigation

### Week 2 Sprint
- [ ] Implement Supabase auth
- [ ] Build config marketplace
- [ ] Create dashboard
- [ ] Add save/load functionality

### Week 3 Sprint
- [ ] Build lesson system
- [ ] Create 10 lessons
- [ ] Add progress tracking
- [ ] Polish UI/UX
- [ ] Bug fixes

### Week 4 (Pre-Launch)
- [ ] Private beta (20 users)
- [ ] Collect feedback
- [ ] Fix critical issues
- [ ] Prepare launch materials

---

## Appendix A: Competitive Analysis

### Direct Competitors
1. **Soundtrap** - Web DAW, too complex for babies
2. **Chrome Music Lab** - Free, simple, but not gamified
3. **Yousician** - Subscription, teaches real instruments
4. **GarageBand** - iOS only, complex interface

### Our Advantages
- ✅ Designed specifically for babies/toddlers
- ✅ Tactile hardware option
- ✅ Classroom-ready
- ✅ No installation required
- ✅ Works on any device

---

## Appendix B: User Research

### Parent Interview Insights (5 parents, 0-3 year olds)
- "I'd pay $10/month if it's educational"
- "Must work on iPad we already have"
- "Want to see what they're learning"
- "Worried about screen time - hardware is better"
- "Would share with other parents if good"

### Teacher Interview Insights (3 music teachers)
- "Need something for 25 kids with 10 tablets"
- "Can't spend more than $500/year"
- "Must track who did what"
- "Prefer tablets over expensive instruments"
- "Would pay for good curriculum"

---

**Status:** Ready for Technical Architecture phase ✅
