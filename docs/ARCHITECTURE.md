# Assessment Architecture and Evidence

## Git flow

`main` is production, `develop` is integration, `release` is UAT promotion, and `feature/customer-search` contains the customer-search work. `hotfix/payment-4.2.1` branches from production, merges into both `main` and `develop`, and is tagged `v4.2.1`. The release history is inspectable with:

```powershell
git log --graph --oneline --decorate --all
git show --stat v4.2.1
```

## Task 1 and Task 2 deployment

`Jenkinsfile` resolves the environment before deployment:

| Environment | Branch | App | DB | Network | Host port | Volume |
| --- | --- | --- | --- | --- | --- | --- |
| DEV | develop | retail-app-dev | retail-db-dev | retail-dev-net | 8081 | retail-db-dev-data |
| UAT | release | retail-app-uat | retail-db-uat | retail-uat-net | 8082 | retail-db-uat-data |
| PRODUCTION | main | retail-app-prod | retail-db-prod | retail-prod-net | 8083 | retail-db-prod-data |

The candidate uses a secondary port, passes health and database connectivity checks, and is removed on failure. Production changes require `CONFIRM_PROD=YES`. Version `4.2.2` is the intentional health-check failure injection.

## Task 3 blue-green deployment

`Jenkinsfile.bluegreen` uses `orders-blue` on port `8081` and `orders-green` on port `8082`, while the active service is exposed on port `8080`. The candidate remains available during validation. Traffic is switched only after health and database checks pass; a failed candidate is removed and the active color is retained.

## Evidence checklist

```powershell
git log --graph --oneline --decorate --all
git tag --list
docker images
docker ps -a
docker inspect <container>
docker network inspect <network>
docker volume inspect <volume>
Invoke-WebRequest http://localhost:<port>/health
```

Jenkins console output must be retained for one successful deployment and the `4.2.2` failed deployment. The failed run must show candidate health failure, candidate removal, previous image restoration or retention, and a failed final build result.
