-- CodeWarden Database Initialization Script
-- This runs automatically when the container first starts

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create test database for tests
CREATE DATABASE postgres_test;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
GRANT ALL PRIVILEGES ON DATABASE postgres_test TO postgres;
