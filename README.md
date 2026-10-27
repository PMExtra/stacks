# Stacks

The personal best practises of containerized services.

Use the `upgrade` script as the only supported entry point for operating stacks:

```sh
./upgrade STACK
```

Run it from the repository root, replacing `STACK` with the stack directory.
See `./upgrade --help` for options and custom commands.

Redis services (`redis`, and the optional Redis components in `sub2api` and
`litellm`) require Docker Engine 25.0+ and Docker Compose 2.20.2+ for
`healthcheck.start_interval`, and Redis 6.2+ for `redis-cli -e` (including when
overriding `TAG`). Checks run every 30s, with a 30s startup grace period, a 5s
startup interval, a 5s timeout and 5 retries. The grace period tolerates initial
failures; it does not force a 30s wait before becoming healthy.

`redis-cli -e ping` also returns nonzero on Redis command errors; connection
errors already fail without `-e`. This is a liveness check, not a complete
authentication test. The optional application components retain `REDISCLI_AUTH`.
The standalone check uses the default local endpoint; if `compose.etc.yaml` or
other local configuration changes authentication, ACL user, port or TLS, adapt
the check and supply credentials securely (for example via `REDISCLI_AUTH`).
Do not put credentials in the healthcheck command. An `unhealthy` status alone
does not trigger a restart under `restart: unless-stopped`.

Validation: Compose 2.40.3 rendered all optional-component combinations of these
three stacks with empty and dummy Redis passwords (40 cases), using
`./upgrade -n STACK config`. No images were pulled or services started; runtime
health transitions and authentication failures were not tested.

PostgreSQL services (`postgres`, and the optional components in `atlassian`,
`litellm` and `sub2api`) use the same healthcheck timing and Engine/Compose
requirements above. `pg_isready -h 127.0.0.1` checks TCP so the official image's
temporary socket-only initialization server does not report ready. User and
database names come from the container environment, defaulting to `postgres`
and the selected user respectively; no password is included in the probe.
The probe returns the original `pg_isready` exit code.

This checks whether PostgreSQL accepts connections, not SQL execution,
authentication, application migrations or write availability. For custom server
configuration that excludes loopback or changes the port/TLS requirements,
override the probe to match. The n8n PostgreSQL component only configures an
external connection and does not add a local PostgreSQL service or probe.

PostgreSQL validation with Compose 2.40.3 covered 237 valid optional-component
and unset/empty/custom user/database combinations, including password-file
components. Standalone PostgreSQL selected exactly one data layout; Confluence
fonts required the Confluence component. Shell mocks checked argument quoting,
fallbacks and unchanged exit-code propagation; no live PostgreSQL readiness tests
were run.
