# CLIProxyAPI (CPA)

Single-container [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)
stack, using the upstream `eceasy/cli-proxy-api` image. No database, Redis,
Home control plane or plugins are configured.

## Initialize

Run from the repository root:

```sh
mkdir -p cpa/mount
chmod 700 cpa/mount
cp -n cpa/config.example.yaml cpa/mount/config.yaml
chmod 600 cpa/mount/config.yaml
```

Edit the staging file `cpa/mount/config.yaml` before importing it into the named
volume. It is not bind-mounted or read directly by the service:

- Replace `access.api-keys` with strong client keys. These authenticate clients
  to CPA, not CPA to an upstream provider. The shipped example is not a usable
  production key; v8.0.77 blocks proxy endpoints with known example keys.
- To enable the Management API, set `management.secret-key` to a different
  strong key. Leaving it empty disables management. Plaintext management keys
  are hashed by CPA; retain the original key securely for login.
- Configure upstream credentials using the management interface or the
  [upstream v8 template](https://github.com/router-for-me/CLIProxyAPI/blob/v8.0.77/config.example.yaml).
  Do not confuse `access.api-keys` with the upstream `api-keys` provider groups.

The template targets v8.0.77. The repository convention defaults to `latest`;
set `TAG` in `cpa/.env` to an upstream published tag when pinning a version.
Check release compatibility before changing versions, especially across majors.
Compose variables are not interpolated inside the mounted application YAML.
`server.port: 8317` is explicit because the local config loader does not supply
this port when it is absent.

Initialize the named config volume once, after editing the staging file:

```sh
./upgrade -n cpa run --rm --no-deps -T --entrypoint sh cpa -ec '
  umask 077
  set -C
  cat > /CLIProxyAPI/config/config.yaml
' < cpa/mount/config.yaml

./upgrade -n cpa config
./upgrade cpa
./upgrade -n cpa logs --tail=100 cpa
```

The shell's `noclobber` setting (`set -C`) refuses an existing `config.yaml`,
including an empty file, rather than overwriting it. If initialization fails,
inspect the volume before retrying. An uninitialized volume has no configuration;
there is no automatic fallback template or unauthenticated bootstrap service.
`run` creates a temporary container and may pull the image if absent; these are
deployment instructions, not actions performed while preparing this stack.

`mount/` and `.env` are ignored by the repository. Never commit real keys,
OAuth files, private configuration or backups.

## Startup versus usable configuration

In normal mode, a missing config file is an error; the image does not copy its
example automatically. Copying the example without editing it can start the
process, but known example client keys put proxy endpoints into safe mode.
An empty management key does not prevent startup: it disables management API
routes unless another supported management credential is supplied. This stack
does not inject such a credential. Upstream credentials are also needed before
inference is usable.

`DEPLOY=cloud` is not configured here. In that mode a missing or whitespace-only
config leaves the process waiting without starting the API server, not serving
a web-based first-run setup.

Configuration remains writable to preserve panel editing. A read-only mount
would make management configuration saves fail. In v8.0.77 a failed startup
write-back of a hashed management key is ignored, but cleanup of conflicting
legacy/v8 fields can fail startup when it cannot write. OAuth credentials live
in the separate writable auth volume; making config read-only would not by
itself make those files read-only.

## Reverse proxy and management

No ports are published by default. Attach the existing reverse-proxy container
to the Compose-managed `cpa` network and forward to `http://cpa:8317`.
Terminate TLS at that proxy; preserve streaming responses and WebSocket
upgrades. Do not buffer SSE responses or use short upstream read timeouts.

The management UI uses `/management.html` on the same listener. The template
sets `management.allow-remote: true` because a reverse-proxy container is not
localhost. A nonempty management key is still required. Restrict management
paths to trusted users/networks at the proxy; do not assume the client API key
protects management. Keep the client and management keys different.

The official panel is downloaded by CPA and may update independently of the
container. Initial panel retrieval requires outbound GitHub access. No custom
panel or separate UI container is included.

## Outbound proxy

For application upstream traffic, add `requests.proxy-url` to the local
configuration, using an HTTP, HTTPS or SOCKS5 URL supported by CPA, for example:

```yaml
requests:
  proxy-url: socks5://proxy:1080
```

The proxy hostname must be reachable from the CPA container. `127.0.0.1` means
the CPA container itself, not the Docker host. This setting is not a Docker
daemon image-pull proxy, and does not guarantee every auxiliary download uses
the same route. Proxy URLs containing credentials are secrets.

## OAuth

For remote Docker deployments, start a login from the protected management
panel. With Codex, after authorizing in your browser, the provider redirects to
`http://localhost:1455/auth/callback`. If that page cannot connect, copy its
complete URL into the panel's callback input and submit it while the login is
still pending. The panel forwards the code/state to CPA over its normal API;
this manual callback route needs no published callback port or SSH tunnel.
Keep the URL private and use the same login attempt; a stale or unrelated state
is rejected. Wait for CPA's final authentication status, not just callback
submission success.

This describes the v8.0.77 backend and current official panel source. Provider
flows and installed panel versions can differ. The panel's automatic localhost
forwarder does not turn a remote browser's localhost into the Docker host.

Alternatively import an existing authorized credential, or use a
provider-supported device-code flow. For Codex:

```sh
./upgrade -n cpa exec cpa ./CLIProxyAPI \
  -config /CLIProxyAPI/config/config.yaml -codex-device-login -no-browser
```

Complete authorization yourself using the URL and code printed by the command.
No account login or credential import is performed by this stack definition.

For browser callback flows only, enable the optional loopback port mapping:

```sh
ln -s optional/compose.oauth.yaml cpa/compose.oauth.yaml
./upgrade cpa
./upgrade -n cpa exec cpa ./CLIProxyAPI \
  -config /CLIProxyAPI/config/config.yaml -codex-login -no-browser
```

The default is port `1455` for Codex. If the browser is on another computer,
forward its localhost port to the Docker host before authorizing:

```sh
ssh -N -L 1455:127.0.0.1:1455 user@docker-host
```

Other providers may require a different callback port or flow. Set
`OAUTH_CALLBACK_PORT` in `cpa/.env` to the required port and recreate the service;
use the matching provider login flag. Changing the mapping alone does not change
CPA's callback listener. Only use `-oauth-callback-port` when the provider permits
the corresponding redirect URI. Do not expose all upstream example ports by
default or bind them publicly. Disable the optional symlink after login if it
is no longer needed, then recreate the service through `./upgrade cpa`.

## Persistence and upgrades

- `config`: named volume containing `config.yaml` and downloaded management
  assets. Directory mounting
  accommodates configuration replacement as well as in-place writes; do not
  mount over `/CLIProxyAPI` or mark configuration read-only.
- `auth`: OAuth credentials and the default local KV database.
- `logs`: CPA's default log directory, including error/request files when used.
  Ordinary application logs use stdout by default. Configure retention if
  enabling file/request logging; logs can contain sensitive data.

All three volumes are Compose-managed and survive container recreation.
`cpa/mount/config.yaml` is only a local staging copy; subsequent panel edits
update the volume, not that file.

### Edit configuration

Prefer the protected management panel after initial setup. For an offline edit,
stop CPA and export the current file before editing it; do not import an old
staging copy over newer panel changes:

```sh
./upgrade -n cpa stop cpa
umask 077
./upgrade -n cpa run --rm --no-deps -T --entrypoint sh cpa -ec \
  'cat /CLIProxyAPI/config/config.yaml' > cpa/mount/config.current.yaml
```

Check the export succeeded, back it up securely, then edit
`cpa/mount/config.current.yaml`. Apply the intentional replacement using a
temporary file in the same volume, then restart:

```sh
./upgrade -n cpa run --rm --no-deps -T --entrypoint sh cpa -ec '
  umask 077
  test -f /CLIProxyAPI/config/config.yaml
  tmp=$(mktemp /CLIProxyAPI/config/config.yaml.XXXXXX)
  trap '\''rm -f "$tmp"'\'' EXIT
  cat > "$tmp"
  test -s "$tmp"
  mv "$tmp" /CLIProxyAPI/config/config.yaml
' < cpa/mount/config.current.yaml
./upgrade cpa
```

Do not restart if export/import failed. Import is an explicit replacement, not
a merge; check the edited YAML before applying it. No real secrets belong in
the repository or in shared command output.

Back up the config and auth volumes securely. Stop CPA with
`./upgrade -n cpa stop cpa` before copying live auth/KV files for a consistent
backup. Record the image version with each backup. Upgrade with `./upgrade cpa`;
do not use `down -v` for routine upgrades. Review new configuration/storage
formats before downgrading and keep a recoverable backup.

No forced architecture or healthcheck is included. The v8.0.77 upstream release
workflow builds Linux amd64 and arm64 images; the live registry manifest was not
checked here. Docker selects an available image platform for the host.
The upstream image does not provide curl/wget, so a probe depending on them would
be invalid. `restart: unless-stopped` handles process exits, not application
readiness. This stack does not claim that Compose validation proves live OAuth,
upstream inference, panel downloads or reverse-proxy behavior.
