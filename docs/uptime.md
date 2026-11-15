

\# Uptime and Health Monitoring



\## Health Endpoint

The application exposes `/healthz/`, returning HTTP 200

with JSON status when Django is running.



\## Restart Policy

Docker Compose uses `restart: unless-stopped` for the web and

database services. Containers restart automatically after failures

unless explicitly stopped.



\## Monitoring

An external uptime monitoring service can periodically request

`/healthz/` and alert administrators when the endpoint is unavailable

or returns a non-200 response.



\## Limitations

The current endpoint checks Django HTTP responsiveness only.

It does not verify database connectivity.

