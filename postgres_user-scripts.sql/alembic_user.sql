-- Create user
CREATE USER alembic_user_url WITH PASSWORD 'alembicpass';

-- Allow connection
GRANT CONNECT ON DATABASE ecoprint TO alembic_user_url;

-- Schema permissions
GRANT USAGE, CREATE ON SCHEMA public TO alembic_user_url;

-- Tables & sequences (current)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO alembic_user_url;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO alembic_user_url;

-- Default privileges (future objects)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON TABLES TO alembic_user_url;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT ALL ON SEQUENCES TO alembic_user_url;
