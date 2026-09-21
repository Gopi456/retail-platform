# Retail Platform — DevOps Assessment

## 1. Project Overview

This project demonstrates a production-style DevOps workflow for an online retail platform.

The implementation covers:

* Git branching and release management
* Feature development
* Emergency payment hotfix
* Git merge conflict creation and resolution
* Docker image creation and container deployment
* Jenkins CI/CD pipeline
* UAT deployment
* Production deployment
* Docker health checks
* Failure injection
* Automatic production rollback

---

## 2. Technology Stack

* Git
* GitHub
* Jenkins
* Docker
* Docker Compose
* Python
* Flask
* Linux/Git Bash
* Windows
* VS Code

---

## 3. Repository Structure

```text
retail-platform/
│
├── app/
│   ├── app.py
│   └── requirements.txt
│
├── tests/
│   └── test_app.py
│
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
└── README.md
```

---

## 4. Application

The application is a lightweight Flask-based retail platform.

Available endpoints:

```text
/
 /health
 /payment
```

The application displays:

* Application version
* Payment status
* Health status

Environment variables are used for deployment configuration:

```text
APP_VERSION
PAYMENT_STATUS
FAIL_HEALTHCHECK
```

---

## 5. Git Branching Strategy

The repository uses the following branches:

```text
main
develop
release/4.3.0
hotfix/payment-4.2.1
```

### main

Production-ready branch.

### develop

Contains ongoing development changes.

### release/4.3.0

Used for release preparation.

### hotfix/payment-4.2.1

Created from production to fix the critical payment defect.

---

## 6. Release History

Initial production release:

```text
v4.2.0
```

Emergency payment hotfix:

```text
v4.2.1
```

Failure-injection testing version:

```text
v4.2.2
```

The `v4.2.2` version was intentionally configured to fail its Docker health check in order to verify automatic rollback.

---

## 7. Payment Hotfix

A critical payment issue was identified in production.

The emergency branch was created:

```text
hotfix/payment-4.2.1
```

The payment behavior was corrected and committed.

The hotfix was then merged into:

```text
main
develop
```

Production was tagged:

```text
v4.2.1
```

---

## 8. Merge Conflict

A deliberate merge conflict was created between the release and development branches in `README.md`.

The conflict was manually resolved and committed.

The final resolution retained the required release and development information.

Example resolved content:

```text
Environment: Development

Release status: 4.3.0 preparation is in progress, including ongoing development changes.
```

This demonstrates:

* Conflict detection
* Manual conflict resolution
* Commit after resolution

---

## 9. Docker Configuration

The application is containerized using Docker.

The image is versioned using the application version:

```text
retail-app:4.2.0
retail-app:4.2.1
retail-app:4.2.2
```

The application listens on:

```text
8081
```

The Docker image includes a health check:

```text
/health
```

The container runs as a non-root user.

---

## 10. Docker Compose

Docker Compose provides:

* Application configuration
* Environment variables
* Docker network
* Health check
* Restart policy
* Resource limits

The application network is:

```text
retail-network
```

Environment-specific configuration is provided through environment variables.

---

## 11. Jenkins Pipeline

Jenkins job:

```text
Retail-Platform-Deployment
```

Pipeline parameters:

```text
DEPLOYMENT_ACTION
ENVIRONMENT
VERSION
CONFIRM_PROD
```

### DEPLOYMENT_ACTION

```text
DEPLOY
ROLLBACK
```

### ENVIRONMENT

```text
UAT
PRODUCTION
```

### CONFIRM_PROD

```text
YES
NO
```

Production deployment is blocked unless:

```text
CONFIRM_PROD=YES
```

---

## 12. Jenkins Deployment Flow

The deployment pipeline performs the following steps:

```text
Parameter Validation
        ↓
Git Tag Validation
        ↓
Identify Selected Git Commit
        ↓
Build Versioned Docker Image
        ↓
Prepare Docker Network
        ↓
Record Previous Production Version
        ↓
Start New Version
        ↓
Health Check
        ↓
UAT / Production Deployment
        ↓
Final Health Check
        ↓
Deployment Verification
```

---

## 13. Production Safety

Before production deployment, Jenkins validates:

```text
ENVIRONMENT=PRODUCTION
CONFIRM_PROD=YES
```

The pipeline records the currently running production image before deployment.

Example:

```text
Previous image  : retail-app:4.2.1
Previous version: 4.2.1
```

The previous version is saved in the Jenkins workspace so that it can be restored automatically if deployment fails.

---

## 14. Automatic Rollback

Automatic rollback was tested using version:

```text
4.2.2
```

Failure injection was enabled using:

```text
FAIL_HEALTHCHECK=true
```

Expected failure sequence:

```text
Build v4.2.2
      ↓
Start new container
      ↓
Health check
      ↓
UNHEALTHY
      ↓
Deployment failure
      ↓
Remove failed v4.2.2
      ↓
Restore v4.2.1
      ↓
Health check
      ↓
HEALTHY
```

The actual Jenkins execution confirmed:

```text
Health check attempt 6/12: unhealthy
```

Jenkins then automatically started rollback.

---

## 15. Rollback Verification

The rollback restored:

```text
Failed Version  : 4.2.2
Restored Version: 4.2.1
Restored Image  : retail-app:4.2.1
Production Health: healthy
```

Jenkins reported:

```text
ROLLBACK VERIFIED SUCCESSFULLY
```

The final production container was:

```text
retail-app-production
```

using:

```text
retail-app:4.2.1
```

with:

```text
healthy
```

status.

The Jenkins build remained:

```text
FAILURE
```

because the requested `4.2.2` deployment failed, even though the automatic rollback successfully restored the previous healthy production version.

---

## 16. Failure Injection Evidence

The failure-injection deployment intentionally used:

```text
Version: 4.2.2
FAIL_HEALTHCHECK=true
```

The health check eventually changed from:

```text
starting
```

to:

```text
unhealthy
```

This triggered the Jenkins failure and automatic rollback mechanism.

---

## 17. Final Production State

After rollback:

```text
Production Image : retail-app:4.2.1
Production Port  : 8081
Production Health: healthy
```

The application remained available on:

```text
http://localhost:8081
```

The health endpoint is:

```text
http://localhost:8081/health
```

---

## 18. Evidence

The assessment evidence includes:

```text
01-local-tests.png
02-initial-git.png
03-develop-feature-history.png
04-release-branch.png
05-hotfix.png
06-v4.2.1-tag.png
07-hotfix-merged-develop.png
08-merge-conflict.png
09-conflict-resolved.png
10-docker-image.png
11-docker-health.png
12-jenkins-parameters.png
13-uat-success.png
14-production-success.png
15-failure-injection.png
16-automatic-rollback.png
17-final-docker.png
18-final-browser.png
```

---

## 19. Final Result

The project demonstrates an end-to-end DevOps workflow covering:

```text
Git
 ↓
GitHub
 ↓
Jenkins
 ↓
Docker Build
 ↓
Health Check
 ↓
UAT
 ↓
Production
 ↓
Failure Detection
 ↓
Automatic Rollback
 ↓
Production Recovery
```

The mandatory failure-injection test successfully demonstrated that an unhealthy deployment is detected and the previous healthy production version is automatically restored.
