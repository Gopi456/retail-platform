# Production Incident Root Cause Record

## Purpose

This document records deployment failures investigated during Task 3 blue-green deployment implementation.

## Incident 1 — Jenkins Build #26

### Failure summary

Build #26 attempted to deploy version 7.9 from Git commit 4c8b6eca10a4657dc8e292cb92d181f0091b05a8.
The existing production version was 7.8 on orders-green.

Candidate orders-blue was successfully started with orders-api:7.9.
Container validation, application health, and database connectivity all passed.

### Root cause

The traffic-switch PowerShell script used Get-Content -Raw, which was not supported by the Jenkins Windows PowerShell environment. Set-Content also failed because the Windows configuration path was parsed incorrectly.

The script printed a success message even though the configuration update failed. Nginx therefore continued serving the previous production container.

### Detection

Traffic verification detected that production was still serving version 7.8 instead of the expected 7.9.

Observed response:

/health -> version 7.8
/db-health -> CONNECTED

### Recovery

Jenkins removed only the candidate orders-blue. The previous active container orders-green was retained.

### Correction

The traffic-switch script was corrected to use Windows-compatible configuration handling and the actual host-mounted Nginx configuration path.

## Incident 2 — Jenkins Build #27

### Failure summary

Build #27 successfully deployed and switched traffic to version 7.9. Production health and database connectivity passed.

The deployment then failed during Deployment Verification.

### Root cause

The Jenkins Windows batch environment could not resolve the findstr command while verifying APP_VERSION.

Failing command:

docker inspect orders-blue --format="{{range .Config.Env}}{{println .}}{{end}}" | findstr /B "APP_VERSION="

Jenkins reported: findstr is not recognized as an internal or external command.

### Detection and recovery

Deployment Verification failed before Old Version Cleanup. The candidate orders-blue was removed and the previous active production container orders-green was retained.

### Correction

The verification command was changed to explicitly call C:\Windows\System32\findstr.exe.

## General Root Cause Findings

The incidents exposed two deployment reliability problems:

1. The traffic-switch configuration was not reliably modified in the configuration actually consumed by Nginx.
2. Windows-specific command resolution caused deployment verification to fail after successful application deployment.

The repaired pipeline separates candidate startup, container validation, application health, database integration, traffic switching, traffic verification, deployment verification, and old-version cleanup.

## Recovery Policy

On failure, Jenkins removes only the candidate and retains the current active production container.

On success, traffic is switched only after candidate validation. The previous active container is removed only after successful traffic and deployment verification.

## Final Successful Resolution — Jenkins Build #28

Build #28 successfully deployed version 7.9.

image=orders-api:7.9 status=running health=healthy
APP_VERSION=7.9
/health -> version 7.9
/db-health -> CONNECTED
Deployment verification passed for orders-green.

The previous active container was removed only after successful traffic and deployment verification.

## Conclusion

The Task 3 deployment process now validates the candidate at container, application, database, traffic, and deployment-verification levels before removing the previous production version. Failed deployments preserve the previous active version and remove only the failed candidate.
