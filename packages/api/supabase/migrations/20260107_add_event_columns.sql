-- Migration: Add missing columns to event_metadata table
-- These columns are required by the telemetry endpoint

-- Add environment column
ALTER TABLE event_metadata
ADD COLUMN IF NOT EXISTS environment TEXT DEFAULT 'production';

-- Add stack_trace column for full error traces
ALTER TABLE event_metadata
ADD COLUMN IF NOT EXISTS stack_trace TEXT;

-- Add index on environment for filtering
CREATE INDEX IF NOT EXISTS idx_events_environment ON event_metadata(environment);
