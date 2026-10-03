# RedApp

[RedApp](https://github.com/PMExtra/RedApp) redistributes Codex CLI and Claude Code
downloads and provides an admin page. This configuration targets RedApp v0.6.2
or later. This stack defaults to `ghcr.io/pmextra/redapp:latest`; Docker selects
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
`REDAPP_DATA`, `REDAPP_LISTEN` or `REDAPP_ALLOWED_HOSTS` empty.

`REDAPP_PUBLIC_URL` remains optional. Published links use **admin override >
`REDAPP_PUBLIC_URL` > safe request origin**. An empty/unset environment value
means no environment default; clearing the admin override restores that default
or request inference. An explicit value must be an HTTP(S) origin without a
subpath. It does not authorize incoming Hosts or change proxy trust.

Set `REDAPP_ALLOWED_HOSTS` to the exact external authority sent by the proxy,
such as `codex.example.internal` or `codex.example.internal:8443`, without a
scheme or path. Lists are comma-separated, allow no wildcards, and replace the
localhost defaults rather than adding to them. Without this setting, only
localhost, 127.0.0.1 and [::1] on the listening port are allowed. The image health
check reads the same configuration and uses the first allowed Host.

The application retains `REDAPP_DATA=/var/lib/redapp` and `REDAPP_LISTEN=:8080`
as defaults. If changing them, update the writable volume target or proxy
routing accordingly. Optional `REDAPP_MAX_ACTIVE_WRITERS`, `REDAPP_MAX_READERS`
and `REDAPP_MAX_ARTIFACT_BYTES` control download capacity (defaults 16, 512 and
4294967296 bytes). Deployment fields use CLI > env > selected file > defaults;
each source must be valid. `REDAPP_CONFIG` can select an explicitly mounted
YAML/JSON file, but is normally omitted: the absent default
`/etc/redapp/config.yaml` is allowed. An explicitly selected missing file fails
startup. PUBLIC_URL has its separate admin precedence described above.

When updating an existing stack, keep `REDAPP_PUBLIC_URL` and
`REDAPP_TRUSTED_PROXIES` in `redapp/.env`, preserving their values, and add the
actual external `REDAPP_ALLOWED_HOSTS`. Shell-exported `REDAPP_*` variables are
no longer automatically forwarded through the old `environment` interpolation;
write them to `.env` instead. Shell exports do not override literal `.env` values
passed through `env_file`. The variable names for public URL,
proxy CIDRs, data and listener have not changed; Host authorization is now
independent of public URL. `REDAPP_BASE_URL` is no longer supported: upstreams
come from built-in application definitions. A custom v0.6.0/v0.6.1 JSON deployment
must keep selecting its mounted file explicitly with `REDAPP_CONFIG`.

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
[operations guide](https://github.com/PMExtra/RedApp/blob/v0.6.2/docs/operations.md)
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
public URL may be unset or empty, or provide an environment default below the
admin override. The root filesystem is read-only, while the data
volume stays writable; the 30s stop grace period covers RedApp's 15s shutdown
wait.

Upgrading from v0.5.x or earlier to v0.6.x requires a separate empty volume:
legacy settings, caches and history are not migrated. Archive the old volume
before selecting the new one. This stack keeps the existing volume name and
does not replace or clear it automatically. Upgrades within v0.6.x, including
v0.6.1 to v0.6.2, reuse the existing new-format volume; no empty replacement is
needed. Before upgrading
`TAG`, stop and back up the whole volume:

```sh
./upgrade --no-up redapp stop
```

Back up using your local volume backup procedure while stopped, then run
`./upgrade redapp`. Restore the whole directory only while stopped; do not copy
only the live SQLite file, delete `instance.lock`, or remove the volume with
`down -v`. Schema downgrades may be rejected.
