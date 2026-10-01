# RedApp

[RedApp](https://github.com/PMExtra/RedApp) caches Codex CLI downloads and provides
an admin page. This stack defaults to `ghcr.io/pmextra/redapp:latest`; Docker
selects the host architecture from the image manifest. Set `TAG` in `redapp/.env`
to pin a release if needed. Anonymous GHCR pull access has not been verified.
If pulling is forbidden, resolve registry access before deployment.

From the repository root, prepare configuration:

```sh
cp redapp/.env.example redapp/.env
```

Edit `redapp/.env`: set `REDAPP_PUBLIC_URL` to the external HTTP(S) origin, such as
`https://codex.example.internal`, without a subpath. Compose rejects an unset or
empty value. The reverse proxy must send a Host matching this origin (including
the port for a non-default port).

The default stack publishes no host ports. For a container reverse proxy, attach
its service to the external Docker network `redapp` and route to `redapp:8080`.
By default, the application trusts no forwarded headers. When forwarded client
IPs are needed, uncomment `REDAPP_TRUSTED_PROXIES` in both `redapp/compose.yaml`
and `redapp/.env`, then set it to the smallest verified proxy peer IP/CIDR set
on the container network. Never use
`0.0.0.0/0`, `::/0`, or a range covering untrusted clients. The proxy must overwrite
incoming forwarding headers. Use HTTPS, disable proxy buffering, allow a 600s
proxy read timeout, and restrict access through the proxy or network policy:
downloads do not require admin login. See the upstream
[operations guide](https://github.com/PMExtra/RedApp/blob/main/docs/operations.md)
for a proxy configuration example.

Validate and deploy through the repository's supported entry point:

```sh
./upgrade --no-up redapp config --quiet
./upgrade redapp
./upgrade --no-up redapp logs redapp
```

Open the configured origin at `/admin/`. The first-start logs show the initial
random admin password only once; protect these logs and change the password
after signing in. No credentials are supplied by this stack.

The named volume `redapp_data` persists the entire `/var/lib/redapp` directory,
including SQLite, WAL/SHM, cached objects and the instance lock. Run only one
instance per local data volume; NFS/SMB shared storage is unsupported. The
image prepares this directory with UID/GID 65532 and mode 0700, runs as that
non-root user, and provides its own health check. Data location and listening
address use the image's defaults (`/var/lib/redapp` and `:8080`). Only the external
public URL is required by this stack so proxy requests match the configured
origin. The root filesystem is read-only, while the data
volume stays writable; the 30s stop grace period covers RedApp's 15s shutdown
wait. Before upgrading `TAG`, stop and back up the whole volume:

```sh
./upgrade --no-up redapp stop
```

Back up using your local volume backup procedure while stopped, then run
`./upgrade redapp`. Restore the whole directory only while stopped; do not copy
only the live SQLite file, delete `instance.lock`, or remove the volume with
`down -v`. Schema downgrades may be rejected.
