-- BabySynth Web - Database Schema
-- Run this in Supabase SQL Editor to set up the database

-- ============================================================================
-- EXTENSIONS
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TABLES
-- ============================================================================

-- Profiles (extends auth.users)
-- One-to-one with Supabase Auth users
CREATE TABLE public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name text,
  avatar_url text,
  subscription_tier text DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'classroom', 'school')),
  subscription_expires_at timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================

-- Configurations
-- User-created Launchpad configurations
CREATE TABLE public.configs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name text NOT NULL,
  description text,
  config_data jsonb NOT NULL,
  is_public boolean DEFAULT false,
  likes_count int DEFAULT 0 CHECK (likes_count >= 0),
  downloads_count int DEFAULT 0 CHECK (downloads_count >= 0),
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_configs_user ON configs(user_id);
CREATE INDEX idx_configs_public ON configs(is_public, likes_count DESC) WHERE is_public = true;
CREATE INDEX idx_configs_created ON configs(created_at DESC);

-- Full-text search on name and description
CREATE INDEX idx_configs_search ON configs USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

CREATE TRIGGER update_configs_updated_at BEFORE UPDATE ON configs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================

-- Config Likes (many-to-many)
-- Tracks which users liked which configs
CREATE TABLE public.config_likes (
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  config_id uuid REFERENCES configs(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  PRIMARY KEY (user_id, config_id)
);

-- Update likes_count when like is added/removed
CREATE OR REPLACE FUNCTION update_config_likes_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE configs SET likes_count = likes_count + 1 WHERE id = NEW.config_id;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE configs SET likes_count = likes_count - 1 WHERE id = OLD.config_id;
  END IF;
  RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_likes_count_on_like AFTER INSERT OR DELETE ON config_likes
FOR EACH ROW EXECUTE FUNCTION update_config_likes_count();

-- ============================================================================

-- Lessons
-- Educational guided lessons
CREATE TABLE public.lessons (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  order_index int NOT NULL UNIQUE,
  title text NOT NULL,
  description text,
  instructions jsonb NOT NULL, -- Array of step objects
  required_config jsonb, -- Optional specific config for this lesson
  unlock_after uuid REFERENCES lessons(id), -- Previous lesson required
  is_premium boolean DEFAULT false,
  estimated_minutes int DEFAULT 5,
  difficulty text DEFAULT 'beginner' CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
  created_at timestamptz DEFAULT now()
);

-- Index for ordering
CREATE INDEX idx_lessons_order ON lessons(order_index);

-- ============================================================================

-- User Progress
-- Tracks which lessons users have completed
CREATE TABLE public.user_progress (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  lesson_id uuid REFERENCES lessons(id) ON DELETE CASCADE NOT NULL,
  completed_at timestamptz,
  score int CHECK (score >= 0 AND score <= 100),
  time_spent int DEFAULT 0, -- seconds
  attempts int DEFAULT 1,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  UNIQUE (user_id, lesson_id)
);

-- Indexes
CREATE INDEX idx_progress_user ON user_progress(user_id);
CREATE INDEX idx_progress_lesson ON user_progress(lesson_id);

CREATE TRIGGER update_progress_updated_at BEFORE UPDATE ON user_progress
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================

-- Play Sessions
-- Analytics tracking for user activity
CREATE TABLE public.play_sessions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  config_id uuid REFERENCES configs(id) ON DELETE SET NULL,
  started_at timestamptz DEFAULT now(),
  ended_at timestamptz,
  notes_played int DEFAULT 0,
  duration int -- seconds (calculated)
);

-- Indexes for analytics queries
CREATE INDEX idx_sessions_user ON play_sessions(user_id, started_at DESC);
CREATE INDEX idx_sessions_config ON play_sessions(config_id);

-- ============================================================================

-- Classrooms (for teachers)
-- Teacher-managed student groups
CREATE TABLE public.classrooms (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  teacher_id uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  name text NOT NULL,
  description text,
  join_code text UNIQUE NOT NULL,
  max_students int DEFAULT 30,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Generate random join code
CREATE OR REPLACE FUNCTION generate_join_code() RETURNS text AS $$
  SELECT UPPER(substr(md5(random()::text), 1, 6));
$$ LANGUAGE SQL;

-- Auto-generate join code if not provided
CREATE OR REPLACE FUNCTION set_join_code()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.join_code IS NULL THEN
    NEW.join_code = generate_join_code();
  END IF;
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER set_classroom_join_code BEFORE INSERT ON classrooms
FOR EACH ROW EXECUTE FUNCTION set_join_code();

CREATE INDEX idx_classrooms_teacher ON classrooms(teacher_id);

CREATE TRIGGER update_classrooms_updated_at BEFORE UPDATE ON classrooms
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================

-- Classroom Students (many-to-many)
-- Maps students to classrooms
CREATE TABLE public.classroom_students (
  classroom_id uuid REFERENCES classrooms(id) ON DELETE CASCADE,
  student_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  joined_at timestamptz DEFAULT now(),
  is_active boolean DEFAULT true,
  PRIMARY KEY (classroom_id, student_id)
);

-- Prevent joining classroom if it's full
CREATE OR REPLACE FUNCTION check_classroom_capacity()
RETURNS TRIGGER AS $$
DECLARE
  current_count int;
  max_count int;
BEGIN
  SELECT COUNT(*), c.max_students INTO current_count, max_count
  FROM classroom_students cs
  JOIN classrooms c ON c.id = cs.classroom_id
  WHERE cs.classroom_id = NEW.classroom_id
  GROUP BY c.max_students;

  IF current_count >= max_count THEN
    RAISE EXCEPTION 'Classroom is full';
  END IF;

  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER check_capacity_before_join BEFORE INSERT ON classroom_students
FOR EACH ROW EXECUTE FUNCTION check_classroom_capacity();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE config_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE lessons ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE play_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE classrooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE classroom_students ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can view own profile, update own profile
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Configs: Users can view public configs or own configs
CREATE POLICY "Anyone can view public configs"
  ON configs FOR SELECT
  USING (
    is_public = true
    OR user_id = auth.uid()
    OR EXISTS (
      -- Teachers can see their students' configs
      SELECT 1 FROM classroom_students cs
      JOIN classrooms c ON c.id = cs.classroom_id
      WHERE cs.student_id = user_id
      AND c.teacher_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert own configs"
  ON configs FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own configs"
  ON configs FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own configs"
  ON configs FOR DELETE
  USING (auth.uid() = user_id);

-- Config Likes: Users can like configs, view all likes
CREATE POLICY "Anyone can view likes"
  ON config_likes FOR SELECT
  USING (true);

CREATE POLICY "Users can insert own likes"
  ON config_likes FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own likes"
  ON config_likes FOR DELETE
  USING (auth.uid() = user_id);

-- Lessons: Everyone can view non-premium lessons, premium requires subscription
CREATE POLICY "Anyone can view free lessons"
  ON lessons FOR SELECT
  USING (
    is_premium = false
    OR EXISTS (
      SELECT 1 FROM profiles
      WHERE id = auth.uid()
      AND subscription_tier IN ('pro', 'classroom', 'school')
      AND (subscription_expires_at IS NULL OR subscription_expires_at > now())
    )
  );

-- User Progress: Users can view/modify own progress
CREATE POLICY "Users can view own progress"
  ON user_progress FOR SELECT
  USING (
    auth.uid() = user_id
    OR EXISTS (
      -- Teachers can see their students' progress
      SELECT 1 FROM classroom_students cs
      JOIN classrooms c ON c.id = cs.classroom_id
      WHERE cs.student_id = user_id
      AND c.teacher_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert own progress"
  ON user_progress FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own progress"
  ON user_progress FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Play Sessions: Users can view/insert own sessions
CREATE POLICY "Users can view own sessions"
  ON play_sessions FOR SELECT
  USING (
    auth.uid() = user_id
    OR EXISTS (
      -- Teachers can see their students' sessions
      SELECT 1 FROM classroom_students cs
      JOIN classrooms c ON c.id = cs.classroom_id
      WHERE cs.student_id = user_id
      AND c.teacher_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert own sessions"
  ON play_sessions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions"
  ON play_sessions FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Classrooms: Teachers can manage own classrooms
CREATE POLICY "Teachers can view own classrooms"
  ON classrooms FOR SELECT
  USING (
    auth.uid() = teacher_id
    OR EXISTS (
      SELECT 1 FROM classroom_students
      WHERE classroom_id = id
      AND student_id = auth.uid()
    )
  );

CREATE POLICY "Teachers can insert classrooms"
  ON classrooms FOR INSERT
  WITH CHECK (auth.uid() = teacher_id);

CREATE POLICY "Teachers can update own classrooms"
  ON classrooms FOR UPDATE
  USING (auth.uid() = teacher_id)
  WITH CHECK (auth.uid() = teacher_id);

CREATE POLICY "Teachers can delete own classrooms"
  ON classrooms FOR DELETE
  USING (auth.uid() = teacher_id);

-- Classroom Students: Students can view, teachers can manage
CREATE POLICY "Anyone can view classroom memberships"
  ON classroom_students FOR SELECT
  USING (
    auth.uid() = student_id
    OR EXISTS (
      SELECT 1 FROM classrooms
      WHERE id = classroom_id
      AND teacher_id = auth.uid()
    )
  );

CREATE POLICY "Students can join classrooms"
  ON classroom_students FOR INSERT
  WITH CHECK (auth.uid() = student_id);

CREATE POLICY "Teachers and students can leave classrooms"
  ON classroom_students FOR DELETE
  USING (
    auth.uid() = student_id
    OR EXISTS (
      SELECT 1 FROM classrooms
      WHERE id = classroom_id
      AND teacher_id = auth.uid()
    )
  );

-- ============================================================================
-- VIEWS (for convenience)
-- ============================================================================

-- Popular configs view
CREATE OR REPLACE VIEW popular_configs AS
SELECT
  c.*,
  p.display_name as author_name,
  p.avatar_url as author_avatar
FROM configs c
JOIN profiles p ON p.id = c.user_id
WHERE c.is_public = true
ORDER BY c.likes_count DESC, c.created_at DESC;

-- User stats view
CREATE OR REPLACE VIEW user_stats AS
SELECT
  u.id as user_id,
  COUNT(DISTINCT ps.id) as total_sessions,
  SUM(ps.duration) as total_play_time_seconds,
  SUM(ps.notes_played) as total_notes_played,
  COUNT(DISTINCT CASE WHEN up.completed_at IS NOT NULL THEN up.lesson_id END) as lessons_completed,
  COUNT(DISTINCT c.id) as configs_created,
  COUNT(DISTINCT cl.config_id) as configs_liked
FROM auth.users u
LEFT JOIN play_sessions ps ON ps.user_id = u.id
LEFT JOIN user_progress up ON up.user_id = u.id
LEFT JOIN configs c ON c.user_id = u.id
LEFT JOIN config_likes cl ON cl.user_id = u.id
GROUP BY u.id;

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Insert default lessons (10 lessons for MVP)
INSERT INTO lessons (order_index, title, description, instructions, difficulty, estimated_minutes) VALUES
(1, 'Find Middle C', 'Learn to locate the middle C note on the Launchpad', '{
  "steps": [
    {"type": "instruction", "text": "Welcome! Let''s find Middle C. It''s the red button in the center."},
    {"type": "action", "text": "Press the red button now!", "highlight": {"x": 4, "y": 4}, "expectedAction": {"button": {"x": 4, "y": 4}, "note": "C"}, "successMessage": "Great job! That''s Middle C!", "tryAgainMessage": "Not quite. Try the red button in the very center."}
  ]
}'::jsonb, 'beginner', 2),

(2, 'Play a Scale', 'Play the C major scale from C to C', '{
  "steps": [
    {"type": "instruction", "text": "A scale is a sequence of notes. Let''s play C-D-E-F-G-A-B-C!"},
    {"type": "action", "text": "Press C (red)", "highlight": {"x": 4, "y": 4}, "expectedAction": {"button": {"x": 4, "y": 4}, "note": "C"}},
    {"type": "action", "text": "Press D (green)", "highlight": {"x": 5, "y": 4}, "expectedAction": {"button": {"x": 5, "y": 4}, "note": "D"}},
    {"type": "action", "text": "Press E (blue)", "highlight": {"x": 6, "y": 4}, "expectedAction": {"button": {"x": 6, "y": 4}, "note": "E"}},
    {"type": "feedback", "text": "Perfect! You played a C major scale!"}
  ]
}'::jsonb, 'beginner', 3),

(3, 'High vs Low', 'Learn to hear the difference between high and low notes', '{
  "steps": [
    {"type": "instruction", "text": "Some notes sound high, some sound low. Let''s explore!"},
    {"type": "action", "text": "Press a LOW note (bottom row)", "successMessage": "Yes! That''s a low note."},
    {"type": "action", "text": "Press a HIGH note (top row)", "successMessage": "Great! That''s a high note."},
    {"type": "feedback", "text": "You can hear the difference! Low notes are deep, high notes are bright."}
  ]
}'::jsonb, 'beginner', 5),

(4, 'Colors and Sounds', 'Match colors to their sounds', '{
  "steps": [
    {"type": "instruction", "text": "Each color makes a different sound. Let''s learn them!"},
    {"type": "action", "text": "Press all the RED buttons", "successMessage": "All red buttons make the same note!"},
    {"type": "action", "text": "Press all the GREEN buttons", "successMessage": "All green buttons sound the same too!"},
    {"type": "feedback", "text": "Colors help you find the same note!"}
  ]
}'::jsonb, 'beginner', 5),

(5, 'Copy the Pattern', 'Repeat a simple melody', '{
  "steps": [
    {"type": "instruction", "text": "I''ll play a pattern. You copy it!"},
    {"type": "instruction", "text": "Listen: C-C-D-E"},
    {"type": "action", "text": "Your turn! Press C", "expectedAction": {"note": "C"}},
    {"type": "action", "text": "Press C again", "expectedAction": {"note": "C"}},
    {"type": "action", "text": "Press D", "expectedAction": {"note": "D"}},
    {"type": "action", "text": "Press E", "expectedAction": {"note": "E"}},
    {"type": "feedback", "text": "Perfect! You copied the pattern!"}
  ]
}'::jsonb, 'intermediate', 7),

(6, 'Make a Melody', 'Create your own simple song', '{
  "steps": [
    {"type": "instruction", "text": "Time to be creative! Make your own melody."},
    {"type": "action", "text": "Play any 5 notes you like", "successMessage": "Beautiful!"},
    {"type": "feedback", "text": "You''re a composer! Music is about expressing yourself."}
  ]
}'::jsonb, 'beginner', 5),

(7, 'Fast vs Slow', 'Explore rhythm and tempo', '{
  "steps": [
    {"type": "instruction", "text": "Music can be fast or slow. Let''s try both!"},
    {"type": "action", "text": "Play C-D-E slowly (one per second)", "successMessage": "Nice slow tempo!"},
    {"type": "action", "text": "Now play C-D-E quickly (fast as you can!)", "successMessage": "So fast!"},
    {"type": "feedback", "text": "You control the speed of music. That''s called tempo!"}
  ]
}'::jsonb, 'beginner', 5),

(8, 'Loud vs Quiet', 'Understand dynamics (coming soon in advanced audio)', '{
  "steps": [
    {"type": "instruction", "text": "Music can be loud or quiet. This is called dynamics."},
    {"type": "action", "text": "Press gently for a quiet sound", "successMessage": "Soft and gentle!"},
    {"type": "action", "text": "Press firmly for a louder sound", "successMessage": "Strong and loud!"},
    {"type": "feedback", "text": "Great! Dynamics add feeling to music."}
  ]
}'::jsonb, 'intermediate', 5),

(9, 'Twinkle Twinkle', 'Play a famous melody', '{
  "steps": [
    {"type": "instruction", "text": "Let''s play Twinkle Twinkle Little Star!"},
    {"type": "action", "text": "C-C-G-G", "successMessage": "Twin-kle twin-kle"},
    {"type": "action", "text": "A-A-G", "successMessage": "lit-tle star"},
    {"type": "action", "text": "F-F-E-E", "successMessage": "How I won-der"},
    {"type": "action", "text": "D-D-C", "successMessage": "what you are!"},
    {"type": "feedback", "text": "You played your first song! 🌟"}
  ]
}'::jsonb, 'intermediate', 10),

(10, 'Free Composition', 'Create and save your own masterpiece', '{
  "steps": [
    {"type": "instruction", "text": "Congratulations! You''ve completed the basics."},
    {"type": "instruction", "text": "Now create your own song. Play anything you want!"},
    {"type": "action", "text": "Play at least 10 notes", "successMessage": "Amazing composition!"},
    {"type": "feedback", "text": "You''re ready to explore! Keep making music!"}
  ]
}'::jsonb, 'beginner', 10);

-- ============================================================================
-- FUNCTIONS FOR API
-- ============================================================================

-- Get trending configs (for marketplace)
CREATE OR REPLACE FUNCTION get_trending_configs(limit_count int DEFAULT 20, offset_count int DEFAULT 0)
RETURNS TABLE (
  id uuid,
  name text,
  description text,
  likes_count int,
  downloads_count int,
  author_name text,
  author_avatar text,
  created_at timestamptz
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id,
    c.name,
    c.description,
    c.likes_count,
    c.downloads_count,
    p.display_name as author_name,
    p.avatar_url as author_avatar,
    c.created_at
  FROM configs c
  JOIN profiles p ON p.id = c.user_id
  WHERE c.is_public = true
  AND c.created_at > now() - interval '30 days' -- Last 30 days
  ORDER BY c.likes_count DESC, c.downloads_count DESC, c.created_at DESC
  LIMIT limit_count
  OFFSET offset_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get user's recent activity
CREATE OR REPLACE FUNCTION get_user_activity(user_uuid uuid, days int DEFAULT 7)
RETURNS TABLE (
  date date,
  play_time_seconds int,
  notes_played int,
  sessions_count int
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    DATE(ps.started_at) as date,
    SUM(ps.duration)::int as play_time_seconds,
    SUM(ps.notes_played)::int as notes_played,
    COUNT(*)::int as sessions_count
  FROM play_sessions ps
  WHERE ps.user_id = user_uuid
  AND ps.started_at > now() - (days || ' days')::interval
  GROUP BY DATE(ps.started_at)
  ORDER BY date DESC;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- DONE!
-- ============================================================================

COMMENT ON DATABASE postgres IS 'BabySynth Web MVP Database - Ready to rock! 🎹';
