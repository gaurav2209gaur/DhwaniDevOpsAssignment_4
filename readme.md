# Grants Stack

A containerized Flask application running behind an Nginx reverse proxy with PostgreSQL as the database.

## Architecture

```text
Client
  |
  | HTTP :8080
  v
Nginx Reverse Proxy
  |
  | HTTP :8000
  v
Flask Application
  |
  | PostgreSQL :5432
  v
PostgreSQL Database
  |
  v
Docker Volume (dbdata)
```

## Services

| Service | Image              | Port | Memory Limit |
| ------- | ------------------ | ---: | -----------: |
| proxy   | nginx:1.25-alpine  | 8080 |        32 MB |
| app     | Custom Flask image | 8000 |       200 MB |
| db      | postgres:16-alpine | 5432 |       256 MB |

The application runs as a non-root user (`appuser`).

## Running the Stack

From the project root:

```bash
docker compose up -d
```

Check the containers:

```bash
docker compose ps
```

Check logs:

```bash
docker compose logs
```

Stop the stack:

```bash
docker compose down
```

## Endpoints

### Health Check

```text
http://localhost:8080/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Application

```text
http://localhost:8080/
```

Example response:

```json
{
  "message": "Stack is running",
  "visit_rows": 6
}
```

## Database Persistence

PostgreSQL data is stored in a named Docker volume:

```yaml
volumes:
  dbdata:
```

The database container mounts the volume at:

```text
/var/lib/postgresql/data
```

Persistence was verified by stopping and removing the containers with:

```bash
docker compose down
```

and starting them again with:

```bash
docker compose up -d
```

The `visit_rows` value increased from `3` to `4` after recreating the containers, confirming that the PostgreSQL data persisted.

## Resource Limits

Current container resource usage was verified with:

```bash
docker stats --no-stream
```

Observed limits:

```text
proxy: 32 MB
app:   200 MB
db:    256 MB
```

## Security

The Flask application runs as a non-root user.

Verified with:

```bash
docker compose exec app whoami
```

Output:

```text
appuser
```

Database passwords are provided through environment variables rather than being hardcoded in the Compose file.

A Git history check was also performed to ensure that real passwords, secrets, or tokens were not committed.

## Docker Images

The project uses:

```text
grants-stack-app:latest
nginx:1.25-alpine
postgres:16-alpine
```

## Most Awkward Requirement

The trickiest part was making sure the application was actually ready before sending requests. Initially, the containers showed as started, but the first curl request failed with a connection reset because the application and proxy were not fully ready yet. PostgreSQL readiness was handled separately with the healthcheck and dependency condition, while the application uses database retry logic instead of relying on a fixed sleep. After the services became ready, the health endpoint and application endpoint worked correctly, and the database persistence test passed.

## Verification

The following checks were completed successfully:

* [ ] Flask application running
* [ ] Nginx reverse proxy working
* [ ] PostgreSQL running and healthy
* [ ] `/health` endpoint returns `status: ok`
* [ ] Application endpoint returns expected response
* [ ] Database persistence verified
* [ ] Application runs as non-root `appuser`
* [ ] Container memory limits configured
* [ ] No real passwords or secrets committed to Git

## Screen Recording

Paste the recording link here:

```text
PASTE YOUR RECORDING LINK HERE
```
