#!/usr/bin/env bash
set -e

# Stop and remove all containers, networks, and volumes
podman-compose down --volumes

# Rebuild images from scratch
podman-compose build --no-cache

# Start up the environmentls
podman-compose up --build 