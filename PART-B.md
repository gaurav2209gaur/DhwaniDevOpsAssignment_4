# Part B — Diagnosis

## Finding 1 — S1: unexplained restarts

**Setting at fault:** `app.deploy.resources.limits.memory: 256M` combined
with no OOM visibility anywhere in the stack.

**Explains:** S1.

**Reasoning:** "Nothing unusual in the app's own logs beforehand" is the
signature of a kernel-level OOM kill, not an application crash — the
process is killed externally (SIGKILL) before it can log anything, and
`restart: unless-stopped` brings it straight back up, masking the event as
a normal restart.

**How I would confirm it:**

docker inspect <app_container_id> --format='{{.State.OOMKilled}}'

run immediately after one of the reported restarts, or:

docker events --filter 'event=die' --filter 'container=app'

looking for exit code 137, or `dmesg | grep -i "killed process"` on the
host itself.

**Fix:** Measure real peak usage with `docker stats` over a working day,
raise the limit above observed peak with headroom, and add a lightweight
memory alert rather than relying on the restart policy to hide it.

---

## Finding 2 — S2: data loss on reboot, not on `restart`

**Setting at fault:** `volumes: - dbdata:/var/lib/mysql/data` on the `db`
service.

**Explains:** S2.

**Reasoning:** The official `mariadb` image stores its data at
`/var/lib/mysql`, not `/var/lib/mysql/data`. Mounting the named volume one
level too deep means MariaDB is actually writing to the container's
writable layer, and the named volume sits beside it, unused. `docker
compose restart` reuses the same container, so the writable layer — and
the data on it — survives. Anything that removes and recreates the
container (which a reboot-triggered `up`/patching cycle can do) throws
that writable layer away, while the untouched named volume is restored
empty.

**How I would confirm it:**

docker inspect <app_container_id> --format='{{.State.OOMKilled}}'

run immediately after one of the reported restarts, or:

docker events --filter 'event=die' --filter 'container=app'

looking for exit code 137, or `dmesg | grep -i "killed process"` on the
host itself.

**Fix:** Measure real peak usage with `docker stats` over a working day,
raise the limit above observed peak with headroom, and add a lightweight
memory alert rather than relying on the restart policy to hide it.

---

## Finding 2 — S2: data loss on reboot, not on `restart`

**Setting at fault:** `volumes: - dbdata:/var/lib/mysql/data` on the `db`
service.

**Explains:** S2.

**Reasoning:** The official `mariadb` image stores its data at
`/var/lib/mysql`, not `/var/lib/mysql/data`. Mounting the named volume one
level too deep means MariaDB is actually writing to the container's
writable layer, and the named volume sits beside it, unused. `docker
compose restart` reuses the same container, so the writable layer — and
the data on it — survives. Anything that removes and recreates the
container (which a reboot-triggered `up`/patching cycle can do) throws
that writable layer away, while the untouched named volume is restored
empty.

**How I would confirm it:**

looking for exit code 137, or `dmesg | grep -i "killed process"` on the
host itself.

**Fix:** Measure real peak usage with `docker stats` over a working day,
raise the limit above observed peak with headroom, and add a lightweight
memory alert rather than relying on the restart policy to hide it.

---

## Finding 2 — S2: data loss on reboot, not on `restart`

**Setting at fault:** `volumes: - dbdata:/var/lib/mysql/data` on the `db`
service.

**Explains:** S2.

**Reasoning:** The official `mariadb` image stores its data at
`/var/lib/mysql`, not `/var/lib/mysql/data`. Mounting the named volume one
level too deep means MariaDB is actually writing to the container's
writable layer, and the named volume sits beside it, unused. `docker
compose restart` reuses the same container, so the writable layer — and
the data on it — survives. Anything that removes and recreates the
container (which a reboot-triggered `up`/patching cycle can do) throws
that writable layer away, while the untouched named volume is restored
empty.

**How I would confirm it:**
docker exec db ls -la /var/lib/mysql # real DB files sit here docker exec db ls -la /var/lib/mysql/data # this will be empty

and reproduce directly:

docker compose down && docker compose up -d

then check whether the data is gone — this reproduces S2 without waiting
for an actual server reboot.

**Fix:** `volumes: - dbdata:/var/lib/mysql` (drop the `/data` suffix).

---

## Finding 3 — S3: broken links + browser security warning after login

**Setting at fault:** `nginx.conf`'s `location /` block is missing
`proxy_set_header Host $host;` and `proxy_set_header X-Forwarded-Proto $scheme;`.

**Explains:** S3.

**Reasoning:** Without an explicit `Host` header, nginx's default when
proxying is to send the upstream address (`app:8000`) as the Host header,
not the original request's host. Any code in the app that builds absolute
URLs from the Host header (redirect targets, "sign in" callback links)
will therefore emit links like `http://app:8000/...` — an address that
only resolves inside the Docker network, exactly matching "an address the
browser cannot reach." Separately, because the load balancer terminates
HTTPS and forwards plain HTTP to this nginx, and nginx doesn't forward
`X-Forwarded-Proto` either, the app has no way of knowing the original
request was HTTPS, so it generates `http://` links from an `https://`
page — the mixed-content pattern that triggers a browser security
warning.

**How I would confirm it:**

curl -sI -H "Host: grants.district.example.gov.in" http:///some-authenticated-route

and inspect any `Location:` header or page body for `app:8000` or
`http://` where `https://` was expected.

**Fix:**

nginx proxy_set_header Host $host; proxy_set_header X-Forwarded-Proto $scheme; proxy_set_header X-Forwarded-Host $host;

---

## Finding 4 — S4: DB unreachable on ~1 in 3 reboots

**Setting at fault:** `app.depends_on: - db` (list form, no health
condition).

**Explains:** S4.

**Reasoning:** Plain `depends_on` only waits for the `db` container
process to *start*, not for MariaDB inside it to finish initializing and
accept connections. On a clean restart MariaDB is usually fast, but after
an unclean shutdown (a reboot) InnoDB sometimes has to run crash recovery
first, which is variable in length. The "roughly 1 in 3" pattern is
exactly what you'd expect from a race between a variable-length DB
startup and a fixed-timing app startup with no retry logic.

**How I would confirm it:** Compare timestamps across a few reboots —

docker compose logs db | grep "ready for connections" docker compose logs app | grep -i "connect"

If the app's first connection attempt timestamp is sometimes before the
db's "ready for connections" line, that's the proof.

**Fix:** Add a healthcheck to `db` and gate `app` on it:

yaml db: healthcheck: test: ["CMD", "mysqladmin", "ping", "-h", "localhost"] interval: 5s retries: 10 app: depends_on: db: condition: service_healthy

Plus, defense in depth: add retry logic inside the app itself so it isn't
solely dependent on Compose's orchestration.

---

## Finding 5 — credential exposure (explains none of S1–S4)

**Setting at fault:** `.env` (containing `MARIADB_ROOT_PASSWORD`) was
committed in commit 3 and deleted in commit 9.

**Explains:** None of S1–S4 directly — this is a separate, standing
security problem.

**Reasoning:** Deleting a file in a later commit does not remove it from
git history; anyone with clone access can still retrieve the plaintext
password from an earlier commit.

**How I would confirm it:**

git log --all --full-history -- .env git show :.env

This will print the plaintext password directly.

**Fix:** Treat the password as already compromised — rotate it
immediately regardless of any history cleanup. Then rewrite history with
`git filter-repo` (or BFG) to strip the file, force-push, and have every
clone re-cloned. Going forward, `.env` stays in `.gitignore` and secrets
are injected via the host environment or a secrets manager, never
committed even temporarily.

---

## What I judge to be deliberate and correct

**`ports: - "127.0.0.1:3306:3306"` on `db`.**

This looks like it shouldn't be there (a DB port exposed at all looks like
a mistake at first glance), but binding it strictly to the loopback
interface exposes it only to processes on the host itself — not the
network — which is exactly what you want for local admin tasks (a cron
job running `mysqldump` from the host, or manual debugging via `mysql
-h127.0.0.1`) without any external exposure risk. Removing it entirely
would make routine operational access harder for no security benefit,
since it's already unreachable from outside the host. I would leave this
exactly as it is.
