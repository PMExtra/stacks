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
