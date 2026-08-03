-- Create user
CREATE USER alembic_user_url WITH PASSWORD 'alembicpass';

-- Allow connection
GRANT CONNECT ON DATABASE ecoprint TO alembic_user_url;

-- Schema permissions
GRANT USAGE, CREATE ON SCHEMA public TO alembic_user_url;

-- Default privileges (future objects)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO alembic_user_url;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO alembic_user_url;
