# Retail Platform DevOps Assessment

This repository contains the Flask retail application and the deployment controls for the Git -> Jenkins -> Docker flow. Every deployment is identified by a Git tag, Docker image tag, and commit SHA.

Release status: 4.3.0 preparation is in progress, including ongoing development changes.

## Quick access for demonstration

Open Jenkins in a browser at [http://localhost:9000](http://localhost:9000). The application URLs depend on which container is running:

| Service | URL | Expected result |
| --- | --- | --- |
| DEV | [http://localhost:8081/health](http://localhost:8081/health) | JSON health response |
| UAT | [http://localhost:8082/health](http://localhost:8082/health) | JSON health response |
| PRODUCTION | [http://localhost:8083/health](http://localhost:8083/health) | JSON health response |
| Customer search | `http://localhost:<port>/customers/search?q=Gopi` | JSON customer result |

The port is the host port. The Flask application always listens on container port `8081`. If port `8081` is already allocated, stop the old container or choose another host port for a local test:

```powershell
docker ps
docker rm -f <old-container-name>
$env:APP_PORT = '18081'
```

## Start the application locally

Run these commands from the repository root in PowerShell. The password is supplied through the shell and is not committed to Git:

```powershell
$env:DB_PASSWORD = 'local-demo-password'
$env:APP_VERSION = '4.2.1'
$env:APP_ENVIRONMENT = 'DEV'
$env:APP_PORT = '18081'
docker build -t retail-app:4.2.1 .
docker compose up -d
docker compose ps
```

Then open:

```text
http://localhost:18081/health
http://localhost:18081/db-health
http://localhost:18081/customers/search?q=Gopi
```

View the outputs in the terminal with `docker compose logs -f app`, or in the browser through the endpoints above. Stop the local stack with:

```powershell
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete the local database volume.

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

### Create the Jenkins job

1. Open [http://localhost:9000](http://localhost:9000) and select **New Item**.
2. Create a **Pipeline** job, for example `retail-platform-deploy`.
3. In **Pipeline**, select **Pipeline script from SCM**.
4. Select **Git** and enter `https://github.com/Gopi456/retail-platform.git`.
5. Use branch `*/assessment/final` for the completed assessment branch.
6. Set the script path to `Jenkinsfile`, save, and select **Build with Parameters**.

Before running the job, create these Jenkins credentials under **Manage Jenkins -> Credentials**:

| Credential ID | Type | Purpose |
| --- | --- | --- |
| `retail-db-credentials` | Username with password | Database password for `Jenkinsfile` |
| `orders-db-credentials` | Username with password | Database password for `Jenkinsfile.bluegreen` |

The Jenkins agent must have Git, Docker Desktop, and Python available. For a Windows agent, the pipeline expects the repository virtual environment at `venv\Scripts\python.exe`.

### Successful deployment demonstration

In **Build with Parameters**, use:

```text
DEPLOYMENT_ACTION = DEPLOY
ENVIRONMENT       = DEV
VERSION           = 4.2.1
CONFIRM_PROD      = NO
RUN_TESTS         = YES
```

Open the build number and select **Console Output**. The important evidence appears in the stages and log: resolved branch/environment, Git commit SHA, image tag, candidate health, database connectivity, final container health, and final result. Jenkins stage output is also visible from the build page’s **Stage View**.

### Automatic rollback demonstration

Run the same job with:

```text
DEPLOYMENT_ACTION = DEPLOY
ENVIRONMENT       = DEV
VERSION           = 4.2.2
CONFIRM_PROD      = NO
RUN_TESTS         = YES
```

Version `4.2.2` intentionally returns HTTP 500 from `/health`. The expected console sequence is: candidate starts, health validation fails, candidate is removed, the previous image is restored or retained, and the Jenkins build ends in failure. This failed console output is required assessment evidence.

### Production protection

For production, use `ENVIRONMENT=PRODUCTION` and set `CONFIRM_PROD=YES`. Any other value is rejected before Docker changes are made. A manual rollback uses `DEPLOYMENT_ACTION=ROLLBACK` and the image version to restore.

### Blue-green job

Create a second Pipeline job from the same repository, set the script path to `Jenkinsfile.bluegreen`, and use branch `*/assessment/final`. It uses `orders-blue`, `orders-green`, and `orders-network`. The candidate is validated before traffic switching; failed candidates are removed while the active color remains available.

For the first blue-green deployment, configure the job with:

```text
ACTION         = DEPLOY
VERSION        = 7.9
CONFIRM_PROD  = YES
```

The job creates `orders-network` and `orders-db` automatically when they do not exist. Add the Jenkins credential `orders-db-credentials` before starting the build. After a successful deployment, check the active endpoint at `http://localhost:8080/health`; candidate ports are `8081` and `8082` during validation.

## Where to find evidence

| Evidence | Location |
| --- | --- |
| Jenkins parameters | Jenkins job -> **Build with Parameters** |
| Successful deployment | Jenkins build -> **Console Output** and **Stage View** |
| Failed deployment and rollback | Jenkins failed build -> **Console Output** |
| Application response | Browser at the selected `/health`, `/db-health`, or search URL |
| Git history and tags | `git log --graph --oneline --decorate --all` and `git tag --list` |
| Images and containers | `docker images`, `docker ps -a`, `docker inspect <container>` |
| Network and volume | `docker network inspect <network>`, `docker volume inspect <volume>` |

To save console evidence for a mentor, use Jenkins build **Console Output -> Download** or copy the console text into the assessment evidence folder. Do not include passwords or credential values.

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
