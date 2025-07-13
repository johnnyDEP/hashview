#!/usr/bin/env bash
set -e

# Stop and remove all containers, networks, and volumes
podman-compose down --volumes

# Rebuild images from scratch
podman-compose build --no-cache

# Start up the environment in the background
echo "Starting containers..."
podman-compose up --build -d

# Run Alembic migrations inside the backend container
echo "Running Alembic migrations..."
podman-compose exec backend alembic upgrade head

echo "Rebuild complete. All containers are up and database is migrated." 