# RedApp

[RedApp](https://github.com/PMExtra/RedApp) redistributes Codex CLI and Claude Code
downloads and provides an admin page. This stack tracks the latest RedApp
and defaults to `ghcr.io/pmextra/redapp:latest`; Docker selects
the host architecture from the image manifest. Set `TAG` in `redapp/.env`
to pin a release if needed. Anonymous GHCR pull access has not been verified.
If pulling is forbidden, resolve registry access before deployment.

From the repository root, optionally prepare application configuration:

```sh
cp redapp/.env.example redapp/.env
```

`compose.yaml` loads the optional `.env` beside it through `env_file`.
Docker Compose 2.24.0 or later is required for `env_file.required: false`
(validated with v2.40.3). Missing `.env` uses application defaults. `./upgrade` changes
into the stack directory, so this relative path also works through that entry
point. No deployment configuration file is mounted or required by default.

Use the same `redapp/.env` for application variables (with their exact `REDAPP_`
names) and optional image `TAG`. Compose uses it for interpolation and passes its
entries into the container; RedApp ignores unrelated names such as `TAG`. Do not
put unrelated sensitive values in this file. The example lists common settings
and defaults; omit settings you do not need. Do not leave numeric limits,
`REDAPP_DATA` or `REDAPP_LISTEN` empty.

`REDAPP_PUBLIC_URL` remains optional. Published links use **admin override >
`REDAPP_PUBLIC_URL` > safe request origin**. An empty/unset environment value
means no environment default; clearing the admin override restores that default
or request inference. An explicit value must be an HTTP(S) origin without a
subpath. It does not authorize incoming Hosts or change proxy trust.

Restrict accepted domains at the reverse proxy. RedApp accepts syntactically
valid Hosts without an application allowlist; keep the proxy's domain restrictions
and forwarding-header controls in place.

The application retains `REDAPP_DATA=/var/lib/redapp` and `REDAPP_LISTEN=:8080`
as defaults. If changing them, update the writable volume target or proxy
routing accordingly. Optional `REDAPP_MAX_WRITERS`, `REDAPP_MAX_READERS`
and `REDAPP_MAX_ARTIFACT_BYTES` control download capacity (defaults 16, 512 and
4GiB). The per-artifact limit accepts go-humanize size syntax or a byte count,
from 1 byte to 1TiB; it is not a total cache quota. `4GiB` is 4294967296 bytes; `4GB` is 4000000000 bytes. Writers and readers
remain positive integer counts. Deployment fields use CLI > env > selected file > defaults;
each source must be valid. `REDAPP_CONFIG` can select an explicitly mounted
YAML/JSON file, but is normally omitted: the absent default
`/etc/redapp/config.yaml` is allowed. An explicitly selected missing file fails
startup. PUBLIC_URL has its separate admin precedence described above.

Shell-exported `REDAPP_*` variables are not automatically forwarded; write them
to `.env` instead. Shell exports do not override literal `.env` values passed
through `env_file`.

The default stack publishes no host ports. For a container reverse proxy, attach
its service to the external Docker network `redapp` and route to `redapp:8080`.
By default, the application trusts no forwarded headers. When forwarded client
IPs or the external HTTPS request origin are needed, set `REDAPP_TRUSTED_PROXIES`
in `redapp/.env` with the smallest verified proxy peer IP/CIDR set on the
container network (comma-separated;
prefer `/32` for IPv4 or `/128` for IPv6). An unset or empty value keeps the
application's default behavior of trusting no forwarded headers. Never use
`0.0.0.0/0`, `::/0`, or a range covering untrusted clients. The proxy must overwrite
incoming forwarding headers. Use HTTPS, disable proxy buffering, allow a 600s
proxy read timeout, and restrict access through the proxy or network policy:
downloads do not require admin login. See the upstream
[operations guide](https://github.com/PMExtra/RedApp/blob/main/docs/operations.md)
for a proxy configuration example.

Before deployment or upgrade, follow the data-volume requirements below.
Validate and deploy through the repository's supported entry point:

```sh
./upgrade --no-up redapp config --quiet
./upgrade redapp
./upgrade --no-up redapp logs redapp
```

Open the external origin at `/admin/`. The first-start logs show the initial
random admin password only once; protect these logs and change the password
after signing in. No credentials are supplied by this stack.

The logical volume `data` (normally `redapp_data`) persists the entire
`/var/lib/redapp` directory,
including SQLite, WAL/SHM, cached objects and the instance lock. Run only one
instance per local data volume; NFS/SMB shared storage is unsupported. The
image prepares this directory with UID/GID 65532 and mode 0700, runs as that
non-root user, and provides its own health check. Data location and listening
address use the image's defaults (`/var/lib/redapp` and `:8080`). The external
public URL may be unset or empty, or provide an environment default below the
admin override. The root filesystem is read-only, while the data
volume stays writable; the 30s stop grace period covers RedApp's 15s shutdown
wait.

For an upgrade requiring a new data format, the operator must provide a fresh
empty volume and retain the old data separately. No settings, caches or history
are imported. This stack does not rename, migrate or delete existing volumes;
confirm the resolved mount before starting. Normal restarts reuse the current
instance's data.

Before upgrading the image or switching volumes, stop the existing instance and
back up its entire current volume:

```sh
./upgrade --no-up redapp stop
```

Back up using your local volume backup procedure while stopped, prepare the
required volume, then run `./upgrade redapp`. Restore only a matching-format
backup into its intended volume while stopped; do not copy
only the live SQLite file, delete `instance.lock`, or remove the volume with
`down -v`. Schema downgrades may be rejected.
