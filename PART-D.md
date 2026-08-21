# Part D — Review of deploy.yml

## Blocking

**`uses: actions/checkout@master`** — pinned to a mutable branch, not a
version tag or SHA. A third-party action can change behaviour, or be
compromised, without any change on our side. Pin to `@v4` or a commit SHA.

**`echo "Authenticating with token $REGISTRY_TOKEN"`** — this prints the
secret directly into build logs. GitHub's log masking is not something to
rely on for a value being manually echoed into a shell string this way.
There's no reason for this line to exist at all — remove it.

**`run: pytest tests/ || true`** — this makes the test step succeed
unconditionally regardless of the actual test outcome, which is precisely
why "it runs green on every push" even when things are broken. Remove
`|| true`. Once removed, a failing test step will naturally stop the
job before push/deploy run (default GitHub Actions behaviour for
sequential steps in one job) — no extra gating logic is needed beyond
this one fix.

**Deploying only the `:latest` tag** — if a bad deploy needs to be rolled
back, there is no previous tagged image to roll back to, because `latest`
has already been overwritten. Tag builds with the git SHA in addition to
`latest`, e.g. `registry.example.com/grants:${{ github.sha }}`, so a
specific known-good build is always retrievable.

## Non-blocking

- No caching for Docker layers or pip — build is slower than it needs to
  be, but not incorrect. Worth adding later.
- No post-deploy health check — after `docker compose up -d`, nothing
  confirms the new container actually came up healthy. A simple
  `curl -f http://prod.example.com/health` after deploy would catch a
  broken deploy immediately instead of waiting for a user to report it.
- No `concurrency:` control — if two pushes land close together, two
  deploy runs could race. Add `concurrency: group: deploy` to serialize
  them.
- SSH host key handling isn't visible here — worth confirming
  `known_hosts` is pinned via a secret rather than disabling strict host
  key checking, but this may already be handled outside this file.
- No environment protection rules (GitHub Environments with required
  reviewers) on the production deploy — a light-touch option worth
  considering, not a hard blocker for a small team.

## Genuinely fine — leave alone

- **`on: push: branches: [main]`** triggering deploy directly — a
  legitimate, common choice for a small team without heavy process
  overhead. Not a problem by itself.
- **`runs-on: ubuntu-latest`** — no reason to self-host runners at this
  scale.
- **Building the image inline in this workflow**, rather than a separate
  build pipeline with artifact hand-off — appropriately simple for one
  deploy target; a multi-job build/push/deploy split would be unnecessary
  ceremony here.
- **SSH + `docker compose pull && docker compose up -d` as the deploy
  mechanism** — this is a genuinely reasonable, appropriately simple
  deploy method for a single production VM. I would resist the urge to
  replace this with anything more elaborate (no Kubernetes, no orchestration
  layer) — it fits the actual scale of what's being deployed.
