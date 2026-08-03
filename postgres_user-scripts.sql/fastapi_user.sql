-- Create user
CREATE USER fastapi_user_url WITH PASSWORD 'fastapipass';

-- Allow connection
GRANT CONNECT ON DATABASE ecoprint TO fastapi_user_url;

-- Schema usage only (NO create)
GRANT USAGE ON SCHEMA public TO fastapi_user_url;

-- Table permissions
GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA public
TO fastapi_user_url;

-- Sequence usage (needed for SERIAL / IDENTITY)
GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA public
TO fastapi_user_url;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES
FOR ROLE alembic_user_url
IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES
TO fastapi_user_url;

ALTER DEFAULT PRIVILEGES
FOR ROLE alembic_user_url
IN SCHEMA public
GRANT USAGE, SELECT
ON SEQUENCES
TO fastapi_user_url;