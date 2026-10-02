# RedApp

[RedApp](https://github.com/PMExtra/RedApp) caches Codex CLI downloads and provides
an admin page. This stack defaults to `ghcr.io/pmextra/redapp:latest`; Docker
selects the host architecture from the image manifest. Set `TAG` in `redapp/.env`
to pin a release if needed. Anonymous GHCR pull access has not been verified.
If pulling is forbidden, resolve registry access before deployment.

From the repository root, optionally prepare configuration:

```sh
cp redapp/.env.example redapp/.env
```

`REDAPP_PUBLIC_URL` is optional with RedApp v0.3.0 or later: leave it unset or
empty to use the application's safe origin inference. To set an explicit origin,
edit `redapp/.env` and set `REDAPP_PUBLIC_URL` to the external HTTP(S) origin, such
as `https://codex.example.internal`, without a subpath. Explicit values retain
the existing behavior: the reverse proxy must send a Host matching this origin
(including the port for a non-default port). If pinning a release older than
v0.3.0, set an explicit origin.

The default stack publishes no host ports. For a container reverse proxy, attach
its service to the external Docker network `redapp` and route to `redapp:8080`.
By default, the application trusts no forwarded headers. When forwarded client
IPs are needed, add `REDAPP_TRUSTED_PROXIES` to `redapp/.env` with the smallest
verified proxy peer IP/CIDR set on the container network (comma-separated;
prefer `/32` for IPv4 or `/128` for IPv6). An unset or empty value keeps the
application's default behavior of trusting no forwarded headers. Never use
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

Open the external origin at `/admin/`. The first-start logs show the initial
random admin password only once; protect these logs and change the password
after signing in. No credentials are supplied by this stack.

The named volume `redapp_data` persists the entire `/var/lib/redapp` directory,
including SQLite, WAL/SHM, cached objects and the instance lock. Run only one
instance per local data volume; NFS/SMB shared storage is unsupported. The
image prepares this directory with UID/GID 65532 and mode 0700, runs as that
non-root user, and provides its own health check. Data location and listening
address use the image's defaults (`/var/lib/redapp` and `:8080`). The external
public URL may be unset or empty with RedApp v0.3.0 or later, or explicitly set
to fix the expected origin. The root filesystem is read-only, while the data
volume stays writable; the 30s stop grace period covers RedApp's 15s shutdown
wait. Before upgrading `TAG`, stop and back up the whole volume:

```sh
./upgrade --no-up redapp stop
```

Back up using your local volume backup procedure while stopped, then run
`./upgrade redapp`. Restore the whole directory only while stopped; do not copy
only the live SQLite file, delete `instance.lock`, or remove the volume with
`down -v`. Schema downgrades may be rejected.
