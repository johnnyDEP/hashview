# Infrastructure Skeleton

This directory contains infrastructure configuration files for running the skeleton app locally or in the cloud.

## Structure
- `docker-compose.yaml`: Compose file for local multi-service development.
- `k8s-deployment.yaml`: Kubernetes manifest for deploying services (minikube/cloud-ready).

## Extension Points
- Add new services or volumes as needed.
- Customize resource limits, environment variables, and networking.

## Notes
- Designed to be compatible with Docker Compose and Kubernetes (minikube).
- Add secrets/configuration as needed for your environment. 