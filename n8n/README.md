# n8n

The base stack runs n8n with SQLite, a persistent `data` volume and no published
ports. It targets n8n 2.35+ and uses `${TAG:-latest}` without fixing a platform.
Use Docker Compose 2.24+ for the optional `env_file` syntax.

Run commands from the repository root through `./upgrade`:

```sh
./upgrade --no-up n8n config --quiet
```

`n8n/.env` is optional and ignored by Git. Put advanced n8n settings there.
`TZ` defaults to `Etc/UTC`; `GENERIC_TIMEZONE` follows it unless explicitly set.
The stack enforces settings-file permissions and retains the image's non-root
user. The readiness check uses wget and the default internal HTTP port 5678
and `/healthz/readiness`; adjust it if changing those settings or internal TLS.

## Data and credentials

The `data` volume mounts `/home/node/.n8n`, including SQLite and the encryption
key n8n generates on first startup. Back up this volume even when using an
external database. To manage the key yourself, set `N8N_ENCRYPTION_KEY` in
`n8n/.env` before first startup and back it up separately. Do not replace an
existing key or delete the volume. Never commit secrets.

## Optional structure

Enable only the extensions needed, using stack-local symlinks:

```sh
ln -s optional/compose.runners.yaml n8n/compose.runners.yaml
ln -s optional/compose.postgres.yaml n8n/compose.postgres.yaml
```

`./upgrade` discovers these links automatically. Validate again after setting
any required variables; the commands above are independent choices.

### Existing HTTPS reverse proxy

Configure these in `n8n/.env`, replacing the example hostname:

```dotenv
N8N_HOST=n8n.example.com
N8N_PROTOCOL=https
N8N_WEBHOOK_URL=https://n8n.example.com/
N8N_EDITOR_BASE_URL=https://n8n.example.com/
N8N_PROXY_HOPS=1
```

Set `N8N_PROXY_HOPS` to the actual trusted proxy count. The last proxy must
correctly set `X-Forwarded-For`, `X-Forwarded-Host` and `X-Forwarded-Proto`, and
support WebSocket upgrades. Use `http://n8n:5678` from a proxy attached to the
`n8n` network. Route only 5678, never the runner broker on 5679. Keep secure
cookies enabled and finish
owner setup before public access. `N8N_WEBHOOK_URL` replaces the deprecated
`WEBHOOK_URL` starting with n8n 2.35.

### External task runners

`compose.runners.yaml` adds an isolated JavaScript/Python runner. Set
`N8N_RUNNERS_AUTH_TOKEN` to your own strong random secret in `n8n/.env`.
The runner gets only its own environment settings, no n8n data volume or
`env_file`. Its root filesystem is read-only, with temporary storage at `/tmp`.

Use this extension for production, real credentials and Python Code nodes.
The base retains internal mode, suitable only for isolated testing without
sensitive data; internal mode is deprecated from n8n 3.0. n8n 2.x enables task
runners by default, so `N8N_RUNNERS_ENABLED` is unnecessary.

n8n and runners share `TAG`. Pin an identical release for reproducible upgrades
and update both together; `latest` is a moving default, not a version lock.
No Redis, queue workers, AI sandbox or Docker socket mount is added.

### Existing PostgreSQL stack

`compose.postgres.yaml` configures only the database connection. It does not
create or manage networks, a database container, volume, database or role, and
has no cross-stack `depends_on`.

Have PostgreSQL join each business stack's network instead of connecting those
stacks to a shared PostgreSQL network, which would make them mutually reachable.
For n8n, configure PostgreSQL to join the `n8n` network using your local
`postgres/compose.override.yaml`. That override is operator-managed and is not
provided here. `DB_POSTGRESDB_HOST` defaults to `postgres` and can be overridden
in `n8n/.env`. Ensure it resolves to PostgreSQL on the `n8n` network.

Before enabling it, have the independent PostgreSQL stack running with an
existing database and suitable application role. `DB_POSTGRESDB_DATABASE` and
`DB_POSTGRESDB_USER` both default to `n8n` and can be overridden in `n8n/.env`.
Set a nonempty `DB_POSTGRESDB_PASSWORD` there; no password default is provided.
These defaults do not create the database or role. PostgreSQL version and
storage configuration belong to that stack, not n8n. The connection uses the
normal internal PostgreSQL port 5432 unless
`DB_POSTGRESDB_PORT` is set in `n8n/.env`.

For a database elsewhere, omit this extension and configure `DB_TYPE=postgresdb`
and the appropriate `DB_POSTGRESDB_*` variables in `n8n/.env`, including TLS
settings where required. Switching from SQLite does not migrate existing data.
Back up the external database and n8n volume together. Prefer PostgreSQL for
sustained production workloads.

## Validation boundary

Compose parsing does not verify PostgreSQL network attachment or DNS resolution,
database existence, credentials, volume permissions, runner registration or
workflow execution. Check those before production use.

## References

- [Docker Compose installation](https://docs.n8n.io/deploy/host-n8n/install-options/install-using-docker-compose)
- [Task runners](https://docs.n8n.io/deploy/host-n8n/configure-n8n/set-up-task-runners)
- [Runner hardening](https://docs.n8n.io/deploy/host-n8n/configure-n8n/security/harden-task-runners)
- [Reverse proxy configuration](https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/configure-webhook-urls-with-reverse-proxy)
- [Encryption key](https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/set-a-custom-encryption-key)
- [Readiness checks](https://docs.n8n.io/deploy/host-n8n/keep-n8n-running/monitor-n8n)
