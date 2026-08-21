# Part C — Decisions under constraints

## C1. Allocate the 4 GB

- OS + Docker daemon overhead: 500 MB
- MariaDB: 1024 MB (`innodb_buffer_pool_size=512M` set explicitly, rest for
  connections/overhead)
- Redis: 200 MB (`maxmemory 150mb`, `maxmemory-policy allkeys-lru` set
  explicitly — never let it grow unbounded)
- App/web workers: 1200 MB (a handful of gunicorn/bench workers, ~250–300MB
  each for a Frappe-style stack)
- Background job workers: 700 MB (1–2 workers; queued jobs can wait, live
  requests can't)
- nginx: 50 MB
- Headroom (page cache, spikes, month-end): ~420 MB unallocated

Total allocated: ~3.67 GB, leaving genuine headroom rather than pinning to
4 GB exactly.

**First thing I'd reduce when it's too tight:** the number of background
job workers, from 2 down to 1. Queued jobs (report generation, notification
sends) can tolerate a slower drain; a slow foreground request cannot.
Gunicorn worker count would be the second thing to touch, only after that.

**Symptom that tells me the allocation was wrong:** containers sitting
pinned at their memory limit continuously in `docker stats` (not just
briefly at month-end), or actual OOM kills in `dmesg`/`docker inspect
OOMKilled`. A single short spike at month-end is expected and fine; a
sustained ceiling is the signal to re-allocate, not just add RAM I don't
have.

## C2. Backups you would be willing to rely on

- **Nightly full logical dump** (`mysqldump`/mariabackup) at 2 AM, when
  usage is "almost none" — stored locally, then pushed off-box immediately
  (rsync/rclone to a separate machine or object store). A single-VM setup
  means a local-only backup protects against nothing if that VM's disk
  fails.
- **Binary log (binlog) shipping** every 15 minutes off-box, giving
  point-in-time recovery between full backups.
- **Retention:** 7 daily, 4 weekly, 3 monthly. (Note: this is backup
  retention, not a workaround for "never hard-delete" — that rule is
  enforced at the application/schema level, e.g. soft-delete flags, not by
  keeping old backups.)
- **RPO: 15 minutes** (worst-case data loss window, bounded by binlog
  shipping interval).
- **RTO: 4 hours** — honest number given no on-site DBA: provisioning a
  replacement, restoring the full dump, replaying binlogs, and verifying
  data takes real, unhurried time by phone-support standards.

**How I know backups actually restore — the part that matters most:** a
weekly automated restore drill. A cron job spins up a throwaway Postgres/
MariaDB container, restores the previous night's dump into it, and runs a
scripted sanity check (row counts on key tables against expected ranges,
or a checksum against a known reference table). If the restore fails, or
row counts are implausible (e.g. zero rows in a table that should hold
thousands), it sends an alert immediately — this is what catches a dump
that "succeeded" but wrote a truncated or empty file, well before an actual
emergency does.

## C3. Respond to a colleague

> Hold on — a few things before you run this.
>
> **During the migration itself:** if this ALTER touches a table that's
> grown over four months of grant records, and MariaDB can't do it as an
> online DDL for this specific change, it will lock that table for the
> full duration — which could be a lot longer than "a few minutes" now that
> the table is bigger than when you tested it. That's a full outage for
> all ~40 users, at 3 PM on a Wednesday, which is close to the worst
> possible time.
>
> **If it fails partway** — a dropped connection over one of the district
> office links, or the disk filling up — you don't get "nothing happened,"
> you get a schema that's partially migrated: some columns added, indexes
> half-built. That's not a state a restore cleanly undoes either.
>
> **On "restore it and we're back to normal":** that backup is from this
> morning. Restoring it throws away every legitimate row entered between
> then and now — and given the audit rule that nothing may ever be
> hard-deleted, silently reverting real beneficiary data is itself a
> compliance problem, not just an inconvenience. It also isn't instant —
> the restore itself takes real time, during which the app is fully down.
> And has that specific backup ever actually been test-restored? If not,
> we don't know it works yet.
>
> **What I'd do instead:** run this in the early-morning low-traffic
> window, not now. Before touching production: take a fresh backup,
> restore it into a scratch container, run the migration there first, and
> time it — so we know exactly how long it takes and that it doesn't break
> anything before it touches real data. Then apply it to production during
> the window, watch logs live, with a tested rollback script ready (not
> just "restore the morning backup").

## C4. Deployment without a second server

**No — true zero-downtime is not achievable here, and I'd say so plainly.**
Zero-downtime deployment fundamentally needs two independent running
copies of the app to swap between; on 2 vCPU / 4 GB with no second machine,
there's no safe way to run two full stacks side by side, and even if
crammed in briefly, having two writers against one MariaDB instance
without real replication expertise is asking for trouble we have no one
on-site to fix.

**Best achievable arrangement:** a short, planned maintenance window,
not zero downtime:
- Pre-pull new images before the window so the swap itself is seconds,
  not minutes.
- For code-only deploys (no schema change), only recreate the `app`
  container — the DB keeps running, cutting the outage to the few seconds
  nginx returns 502s while `app` restarts.
- Schedule this at a fixed time during the "almost none overnight" window,
  communicated to district offices in advance.
- Schema-migration deploys get a longer, explicitly announced window (see
  C3), not folded into the routine deploy.

**What I'd tell the department:** true zero-downtime needs redundant
infrastructure we don't have budget for this year. What I can realistically
commit to is a brief (single-digit-minutes), scheduled, off-hours
interruption — which, given real usage overnight is near zero, has
effectively the same impact on users as zero-downtime would. If genuine
zero-downtime becomes a hard requirement, that's the case for a second VM
next budget cycle.
