# Production Incident Root Cause Record

## Incident

The original deployment process could report a running container without proving that the application was reachable. A candidate could also be started on the wrong port or network, leaving users without a valid production endpoint.

## Investigation commands

```powershell
git rev-parse HEAD
git branch --show-current
docker ps -a
docker logs orders-blue
docker inspect orders-blue
docker inspect orders-network
docker exec orders-blue python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8081/health').status)"
Invoke-WebRequest http://localhost:8080/health
```

## Root cause and correction

The failure class is a deployment-validation gap: container state was treated as application availability. The repaired pipeline separates candidate startup from traffic switching and validates the container image, network attachment, health endpoint, database connectivity, and external response before removing the active version.

## Recovery

On a failed candidate, Jenkins removes only the candidate. The active color remains serving traffic. The console records the active color, candidate color, image tag, Git SHA, health result, and final build result.
