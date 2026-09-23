# Task 3 - Blue-Green Architecture

## Architecture

Git Repository -> Jenkins -> Docker Image -> Blue/Green Candidate -> Nginx -> Production

Blue:
- Container: orders-blue
- Host port: 18081
- Container port: 8081

Green:
- Container: orders-green
- Host port: 18082
- Container port: 8081

Nginx:
- Container: orders-proxy
- Host port: 18080
- Container port: 8080

## Components

| Component | Purpose |
|---|---|
| orders-blue | Blue application container |
| orders-green | Green application container |
| orders-proxy | Nginx production traffic proxy |
| orders-db | PostgreSQL database |
| orders-network | Shared Docker network |
| orders-db-data | Persistent database volume |

## Docker Network

All application, proxy and database containers communicate through orders-network.

Network type: Docker bridge

Subnet: 172.27.0.0/16

Connected components:
- orders-blue
- orders-green
- orders-proxy
- orders-db

## Database Persistence

Database container: orders-db

Persistent volume: orders-db-data

Mount: /var/lib/postgresql/data

The database volume remains independent of application container replacement.

## Jenkins Pipeline

Jenkins job: Retail-Platform-Task3-BlueGreen

Pipeline stages:

1. Checkout
2. Validate Version
3. Unit/Application Test
4. Docker Build
5. Docker Image Validation
6. Start Candidate
7. Container Validation
8. Application Health Check
9. Integration Check
10. Traffic Switch
11. Traffic Verification
12. Deployment Verification
13. Old Version Cleanup

## Blue-Green Deployment

The pipeline identifies the active color and starts the opposite color as the candidate.

The candidate runs while the current production version remains available.

The candidate is validated before production traffic is switched.

Validation includes:
- Container status
- Docker image
- Docker network
- Application health
- Database connectivity
- Traffic verification
- Deployment verification

## Traffic Switching

Nginx uses the active application container as its upstream.

Blue upstream: orders-blue:8081

Green upstream: orders-green:8081

Production entry point: http://localhost:18080

Traffic is switched only after candidate validation succeeds.

## Failure Recovery

If candidate deployment or validation fails:

Candidate failure
-> Remove candidate
-> Retain previous active container
-> Keep previous production traffic
-> Jenkins build fails

The previous active version is removed only after successful traffic and deployment verification.

## Version and Git Traceability

Git tag: v7.9

Release commit:
4c8b6eca10a4657dc8e292cb92d181f0091b05a8

Jenkins Build: #28

Docker image: orders-api:7.9

Application version: APP_VERSION=7.9

Production container: orders-green

Production health: version 7.9

## Successful Deployment Evidence

Jenkins Build #28 successfully deployed version 7.9.

Deployment verification:
- image=orders-api:7.9
- status=running
- health=healthy
- APP_VERSION=7.9

Application health:
/health -> version 7.9

Database health:
/db-health -> CONNECTED

The previous active container was removed only after successful traffic and deployment verification.

## Incident Documentation

Task 3 deployment failures are documented in:

docs/INCIDENT-RCA.md

Documented incidents:
- Build #26
- Build #27

Build #28 records the successful resolution.