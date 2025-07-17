#!/usr/bin/env python3
import subprocess
import time

COMPOSE = ["podman-compose"]

# Step 1: Stop and remove all containers, networks, and volumes
subprocess.run(COMPOSE + ["down", "--volumes"], check=True)

# Step 2: Rebuild images from scratch
subprocess.run(COMPOSE + ["build", "--no-cache"], check=True)

# Step 3: Start up the environment in the background
print("Starting containers...")
subprocess.run(COMPOSE + ["up", "--build", "-d"], check=True)

# Step 4: Wait for backend container to be running
print("Waiting for backend container to be running...")
while True:
    result = subprocess.run(COMPOSE + ["ps"], capture_output=True, text=True)
    if "backend" in result.stdout and "Up" in result.stdout:
        print("Backend container is running.")
        break
    print("Backend not up yet, waiting 10 seconds...")
    time.sleep(10)

# Step 5: Check if Alembic versions directory is empty in the backend container
print("Checking for existing Alembic migrations...")
check_versions = subprocess.run(
    COMPOSE + ["exec", "backend", "bash", "-c", "[ \"$(ls -A alembic/versions)\" ] && echo 'not empty' || echo 'empty'"],
    capture_output=True, text=True, check=True
)

if "empty" in check_versions.stdout:
    print("No Alembic migrations found. Generating initial migration...")
    subprocess.run(COMPOSE + ["exec", "backend", "alembic", "revision", "--autogenerate", "-m", "Initial schema"], check=True)
else:
    print("Alembic migrations found.")

# Step 6: Run Alembic migrations inside the backend container
print("Running Alembic migrations...")
subprocess.run(COMPOSE + ["exec", "backend", "alembic", "upgrade", "head"], check=True)

# Step 7: Insert sample data for UI testing
print("Inserting sample data...")
subprocess.run(COMPOSE + ["exec", "backend", "python3", "insert_sample_data.py"], check=True)

print("Rebuild complete. All containers are up, database is migrated, and sample data is inserted.") 