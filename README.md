# Retail Platform — DevOps Assessment

## Project Overview

This repository demonstrates a complete DevOps implementation for a retail platform application using **Git, Jenkins, Docker, automated testing, CI/CD pipelines, deployment validation, rollback handling, and production-style deployment strategies**.

The assessment is divided into three tasks. Each task focuses on different aspects of source control, continuous integration, containerization, deployment automation, troubleshooting, and production recovery.

### Technology Stack

* **Source Control:** Git / GitHub
* **CI/CD:** Jenkins
* **Containerization:** Docker / Docker Compose
* **Application:** Python
* **Testing:** Pytest
* **Web Server / Reverse Proxy:** Nginx
* **Database:** PostgreSQL
* **Scripting:** PowerShell / Shell
* **Operating Environment:** Windows / Docker Desktop

---

# Task 1 — Git Workflow and Source Control

## Objective

Task 1 focuses on applying Git-based development practices required for a collaborative software project.

The implementation demonstrates:

* Feature branch creation
* Git branching strategy
* Commit management
* Merging branches
* Rebasing
* Merge conflict resolution
* Tags and release management
* Git history inspection
* Recovery from Git mistakes
* Working with remote GitHub repositories

## Git Operations Demonstrated

The task covers practical Git operations including:

```bash
git branch
git checkout
git switch
git add
git commit
git merge
git rebase
git log
git diff
git tag
git reset
git reflog
git push
git pull
```

## Key Outcomes

* Changes are developed through separate branches.
* Commits provide traceability for individual changes.
* Merge and rebase workflows are demonstrated.
* Conflicts are identified and resolved.
* Release tags provide identifiable versions.
* Git history and recovery mechanisms are demonstrated.
* The repository is maintained in a structured and traceable manner.

---

# Task 2 — Jenkins CI/CD and Docker Automation

## Objective

Task 2 focuses on building an automated CI/CD workflow that connects GitHub, Jenkins, Docker, application testing, and deployment.

## CI/CD Workflow

The overall workflow is:

```text
Developer
    |
    v
GitHub Repository
    |
    v
Jenkins
    |
    +--> Checkout Source
    |
    +--> Validate Application
    |
    +--> Run Tests
    |
    +--> Build Docker Image
    |
    +--> Validate Docker Image
    |
    +--> Start Container
    |
    +--> Validate Application
    |
    v
Docker Application
```

## Jenkins Automation

The Jenkins pipeline demonstrates:

* Source-code checkout
* Git-based pipeline execution
* Automated application testing
* Docker image creation
* Docker container execution
* Container validation
* Application health validation
* Parameterized execution
* Conditional pipeline behaviour
* Failure handling
* Deployment verification
* Build status reporting

Required command failures are allowed to fail the pipeline rather than being silently ignored.

## Docker

The application is packaged and executed using Docker.

The implementation demonstrates:

* Dockerfile-based image creation
* Image tagging
* Container lifecycle management
* Port mapping
* Environment variables
* Docker networks
* Container health checks
* Application connectivity validation
* Docker Compose configuration

Example image format:

```text
orders-api:<version>
```

Versioned image tags are used instead of relying exclusively on the `latest` tag.

## Testing

Application tests are executed as part of the automated workflow.

Example:

```bash
pytest -q
```

Successful tests are required before the deployment process continues.

## Key Outcomes

* GitHub acts as the source repository.
* Jenkins automates the CI/CD workflow.
* Docker provides consistent application packaging and execution.
* Application tests are executed automatically.
* Deployment failures are detected by the pipeline.
* Application and container validation are performed before deployment completion.

---

# Task 3 — Production Incident, Pipeline Recovery and Blue-Green Deployment

## Objective

Task 3 simulates a production deployment incident in which a newly deployed application version becomes unavailable.

The task focuses on:

* Production incident investigation
* Root-cause analysis
* Jenkins pipeline recovery
* Deployment validation
* Blue-green deployment
* Traffic switching
* Automatic rollback
* Version traceability
* Production verification

---

## Production Architecture

The deployment architecture is:

```text
GitHub
   |
   v
Jenkins
   |
   v
Docker Image
   |
   +-------------------+
   |                   |
   v                   v
 BLUE                GREEN
orders-blue       orders-green
   |                   |
   +---------+---------+
             |
             v
           Nginx
             |
             v
        Production
             |
             v
        PostgreSQL
```

The blue-green strategy allows the existing production version to remain available while a new candidate version is started and validated.

---

## Blue-Green Deployment

The deployment uses two application environments:

| Environment | Container      | Host Port | Container Port |
| ----------- | -------------- | --------: | -------------: |
| BLUE        | `orders-blue`  |     18081 |           8081 |
| GREEN       | `orders-green` |     18082 |           8081 |

The Nginx production proxy exposes the application through the production endpoint.

```text
Nginx
  |
  +--> BLUE
  |
  OR
  |
  +--> GREEN
```

Only the validated environment receives production traffic.

---

## Deployment Flow

The Task 3 pipeline contains meaningful deployment stages:

```text
Checkout
   ↓
Validate Version
   ↓
Unit/Application Test
   ↓
Docker Build
   ↓
Docker Image Validation
   ↓
Start Candidate
   ↓
Container Validation
   ↓
Application Health Check
   ↓
Integration Check
   ↓
Traffic Switch
   ↓
Old Version Cleanup
   ↓
Deployment Verification
```

### Deployment Rules

### Successful Deployment

```text
Candidate starts
      ↓
Container validation
      ↓
Health check
      ↓
Application validation
      ↓
Database integration check
      ↓
Traffic switch
      ↓
Deployment verification
      ↓
Remove old version
```

### Failed Deployment

```text
Candidate starts
      ↓
Validation fails
      ↓
Candidate removed
      ↓
Current production version retained
```

This prevents an unsuccessful candidate from replacing the existing production version.

---

# Production Incident Investigation

The production incident investigation includes:

* Jenkins console analysis
* Git commit verification
* Branch verification
* Docker container status
* Container logs
* Environment variables
* Port mappings
* Docker network inspection
* Application health checks
* Database connectivity
* Process/application port verification
* Traffic verification

The investigation process is documented in:

```text
docs/INCIDENT-RCA.md
```

---

# Pipeline Recovery

Two deployment failures were investigated during pipeline recovery.

## Failure Investigation 1

The candidate deployment successfully started and passed application/database validation, but the traffic-switch operation failed because of a Windows PowerShell compatibility/path handling issue.

The pipeline correctly:

* Detected the traffic-switch failure
* Stopped the deployment
* Removed the candidate container
* Preserved the existing production version

The traffic-switch implementation was then corrected.

---

## Failure Investigation 2

After traffic switching was successfully implemented, deployment verification failed because the Windows `findstr` executable was not resolved correctly by the Jenkins environment.

The pipeline correctly:

* Detected the verification failure
* Prevented old-version cleanup
* Removed the candidate
* Preserved the current production version

The verification command was corrected to use the explicit Windows executable path.

---

# Successful Deployment

After the pipeline corrections, the deployment completed successfully.

The final production deployment demonstrated:

```text
Application Version: 7.9
Container: orders-green
Image: orders-api:7.9
Health: healthy
Database: CONNECTED
```

Production health verification:

```text
/health
```

returns the deployed application version and production status.

Database verification:

```text
/db-health
```

confirms database connectivity.

---

# Docker Network and Database Persistence

The application components communicate through the Docker network:

```text
orders-network
```

The deployment includes:

```text
orders-proxy
orders-green / orders-blue
orders-db
```

The PostgreSQL database uses a named Docker volume:

```text
orders-db-data
```

This provides persistent database storage independent of the application container lifecycle.

---

# Version and Git Traceability

Each deployment is associated with:

* Application version
* Docker image tag
* Git commit SHA
* Jenkins build
* Release tag

Example release:

```text
Application Version: 7.9
Docker Image: orders-api:7.9
Git Release Tag: v7.9
```

The release tag `v7.9` is associated with the corresponding release commit, providing traceability from the deployed application back to source control.

The application also exposes its version through the health endpoint.

---

# Failure Recovery Policy

The deployment follows a simple production recovery policy.

### PASS

```text
Candidate validated
       ↓
Traffic switched
       ↓
Production verified
       ↓
Old version removed
```

### FAIL

```text
Candidate validation fails
       ↓
Candidate removed
       ↓
Current production retained
```

This ensures that a failed deployment does not automatically remove a known working production version.

---

# Repository Structure

The repository contains the main application, deployment, testing, and documentation components.

```text
retail-platform/
│
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── customers.py
│   ├── database.py
│   └── requirements.txt
│
├── tests/
│   ├── __init__.py
│   └── test_app.py
│
├── scripts/
│   ├── start-demo.ps1
│   ├── stop-demo.ps1
│   └── switch-traffic.ps1
│
├── docs/
│   ├── ARCHITECTURE.md
│   └── INCIDENT-RCA.md
│
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── Jenkinsfile.bluegreen
├── nginx/
│   └── default.conf
├── README.md
└── .gitignore
```

---

# DevOps Flow

The complete project demonstrates the following DevOps lifecycle:

```text
Git
 |
 | Source Control
 v
GitHub
 |
 | Source Repository
 v
Jenkins
 |
 | CI/CD Automation
 v
Automated Tests
 |
 v
Docker Build
 |
 v
Docker Image
 |
 v
Container Validation
 |
 v
Deployment
 |
 v
Health & Integration Checks
 |
 v
Traffic Management
 |
 v
Production Verification
 |
 v
Release Traceability
```

---

# Key DevOps Practices Demonstrated

Across all three tasks, the project demonstrates:

* Version-controlled development
* Git branching and release management
* Automated CI/CD
* Automated application testing
* Docker image creation
* Container lifecycle management
* Health checks
* Environment configuration
* Docker networking
* Database connectivity
* Production deployment validation
* Blue-green deployment
* Failure detection
* Automatic candidate cleanup
* Production rollback protection
* Git commit traceability
* Immutable versioned Docker images
* Incident investigation
* Root-cause documentation

---

# Assessment Deliverables

The repository provides the following assessment artifacts:

* Git repository
* Git branches and history
* Release tags
* Jenkins pipelines
* Dockerfile
* Docker Compose configuration
* Application source
* Automated tests
* Deployment scripts
* Nginx configuration
* Blue-green deployment implementation
* Deployment verification
* Incident RCA
* Architecture documentation
* Successful deployment evidence
* Failed deployment investigations
* Rollback/recovery evidence
* Docker network evidence
* Database volume evidence

---

# Conclusion

This project demonstrates a complete progression from **Git-based source control to automated Jenkins CI/CD, Docker-based application deployment, production incident investigation, and blue-green production deployment**.

The implementation emphasizes repeatability, traceability, automated validation, controlled traffic switching, and safe recovery from deployment failures.
