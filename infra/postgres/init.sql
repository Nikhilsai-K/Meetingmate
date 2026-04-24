-- Initial Postgres setup.
-- Runs once on container first-boot. Creates required extensions.
-- Schema itself is managed by Alembic migrations under apps/api/alembic.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Separate role used by the API so RLS can enforce per-user isolation.
-- The API connects as this role and issues `SET LOCAL app.user_id = '<uuid>'`
-- on every request. Row-level security policies reference current_setting('app.user_id').
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'meetingmate_app') THEN
    CREATE ROLE meetingmate_app LOGIN PASSWORD 'meetingmate_app';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE meetingmate TO meetingmate_app;
