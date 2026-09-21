# Retail Platform DevOps Assessment

This repository contains the Flask retail application and the deployment controls for the Git -> Jenkins -> Docker flow. Every deployment is identified by a Git tag, Docker image tag, and commit SHA.

Release status: 4.3.0 preparation is in progress, including ongoing development changes.

## Application

The service listens on container port `8081` and exposes `/health`, `/db-health`, `/payment`, and `/customers/search?q=...`. `/health` reports the application version and `APP_ENVIRONMENT`. The customer search path uses PostgreSQL through the `DB_HOST` service name; it does not use `localhost` inside a container.

## Local multi-environment stack

The Compose file runs separate app and PostgreSQL containers on an environment-specific bridge network and named database volume. Supply the database password without committing it:

```powershell
$env:DB_PASSWORD = 'use-a-local-secret'
$env:APP_VERSION = '4.2.1'
$env:APP_ENVIRONMENT = 'DEV'
docker compose up -d
docker compose ps
docker inspect retail-db-dev-data
docker network inspect retail-dev-net
```

Use `APP_CONTAINER`, `DB_CONTAINER`, `APP_NETWORK`, `APP_PORT`, and `DB_VOLUME` to select UAT or production names and ports. The host port changes per environment, while the application always listens on `8081` inside its container.

## Jenkins pipeline

`Jenkinsfile` accepts `DEPLOYMENT_ACTION`, `ENVIRONMENT`, `VERSION`, `CONFIRM_PROD`, and `RUN_TESTS`. The `retail-db-credentials` Jenkins username/password credential supplies the database password; it is never stored in the image or repository.

The deployment stages validate the Git tag, record the commit, build an immutable image, start a candidate on a secondary port, validate application and database connectivity, then switch traffic. A failed candidate is removed while the current container remains available. Production requires `CONFIRM_PROD=YES`.

For the mandatory failure demonstration, deploy version `4.2.2`. Jenkins sets `FAIL_HEALTHCHECK=true`, the candidate health request fails, and the post-failure action removes the candidate without removing the current deployment. The console output should retain the old image, candidate image, health result, and final container state.

## Evidence commands

```powershell
git log --graph --oneline --decorate --all
git tag --list
docker images retail-app
docker ps -a
docker inspect retail-app-dev --format '{{.Config.Image}} {{.State.Health.Status}}'
docker network inspect retail-dev-net
docker volume inspect retail-platform_retail-db-dev-data
```

Run the application checks with the repository interpreter:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```
