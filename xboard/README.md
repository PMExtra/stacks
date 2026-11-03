# XBoard

[XBoard](https://github.com/cedar2025/Xboard) manages users, subscriptions,
billing and node configuration. This stack follows its current single-container
image: Octane, Horizon, Redis, the WebSocket server and an internal HTTP Caddy
router. SQLite is the default installation choice. No host ports are published;
an independent reverse proxy on the `xboard` Docker network terminates TLS.
Operate the stack from the repository root with `./upgrade`.

## Initialize

Requires Docker with Compose v2, GNU find, and a TLS reverse proxy. The upstream
XBoard image build targets `linux/amd64` and `linux/arm64`; a read-only manifest
check on 2026-10-31 confirmed both architectures for `ghcr.io/cedar2025/xboard:latest`.
No architecture is forced here. Recheck the manifest
of your chosen image tag before deployment.

```sh
cp xboard/.env.example xboard/.env
mkdir -p xboard/mount
touch xboard/mount/app.env
chmod 600 xboard/.env xboard/mount/app.env
./upgrade -n xboard config --quiet
./upgrade -n xboard run --rm -e ENABLE_SQLITE=true xboard php artisan xboard:install
```

The installer prompts for an administrator email and generates the application
key, admin password and private admin URL. Save its output securely. Check that
`mount/app.env` contains `INSTALLED=1` or `INSTALLED=true` before continuing:
the installer can report errors without a nonzero exit code. Never run it on a
populated database to reset an account. The writable file must exist before
installation; Compose deliberately refuses to create a directory in its place.

`xboard/.env` controls Compose; `xboard/mount/app.env` is the separate Laravel
configuration written by the installer. Do not copy the Compose example into
`app.env` or use upstream's example application key. Set `APP_URL` in `app.env`
to your public HTTPS panel URL and configure the panel's site/subscription URLs
consistently. Keep `APP_DEBUG=false`. Both local files are ignored by Git.

```sh
./upgrade xboard
./upgrade -n xboard logs --tail=100 xboard
```

Confirm all supervisor processes and migrations are healthy in logs and verify
the admin login/API through the proxy. No synthetic healthcheck is supplied:
a listening HTTP socket alone does not prove queues or node synchronization work.

## Redis, database and nodes

Redis is required by Horizon queues and other XBoard functionality, not merely
an optional performance cache. By default the embedded Redis listens only on
`/data/redis.sock`, with data persisted in the `redis` volume. Disabling it without
a replacement can break queue processing, traffic accounting and cache-dependent
operations. It does not turn XBoard into a Redis-free application.

For external Redis, set `ENABLE_REDIS=false` in the Compose `.env` and configure
`REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` in `mount/app.env`; ensure the endpoint
is reachable from the container. Keep Horizon enabled. For a **fresh** external
Redis installation, use the interactive installer instead of the quick command:

```sh
./upgrade -n xboard run --rm -e ENABLE_REDIS= xboard php artisan xboard:install
```

Choose the database and decline embedded Redis, then supply the external Redis
connection. The empty override is intentional: this version's installer treats
the nonempty string `false` as truthy, while supervisor expects `false` at runtime.
An external Redis must already be running during this interactive connection test.
For external SQL, also use the interactive installer and provision a dedicated
database first. This stack does not provision external databases or networks.

XBoard is the control panel; xray-core handles proxy traffic on node hosts.
A compatible, maintained node backend/agent with support for the selected
XBoard API/protocol fetches node configuration and authorized users,
applies them to its core and reports traffic/status to XBoard. A standalone
xray-core does not automatically sync with XBoard. Node agents need the panel
URL, node ID/type and API credentials; protect them and verify version support.
This stack does not deploy nodes, open proxy protocol ports or attach the
repository's `xray` stack. Redis is not a replacement for this node API link.

## Native themes

Use XBoard's built-in frontend initially. Compatible native theme packages can
be uploaded and selected through XBoard's theme management. The inspected
upstream requires a ZIP containing `config.json` with a theme name and
`dashboard.blade.php`; a generic static frontend build is not an installable
native theme. Only install trusted packages compatible with your XBoard version:
Blade templates run as part of the application.

The `theme` volume persists user-installed themes at `/www/storage/theme`.
Built-in themes under `/www/theme` remain supplied by the image. XBoard copies
active theme assets to `/www/public/theme`; that generated directory is not
mounted over the image's public directory. Theme settings also live in the
database, so back up both the database and theme volume before theme changes.

For an upgrade, retain the previous package and upload a reviewed newer version
through theme management. The inspected uploader rejects same/older versions
and attempts to preserve user settings during upgrades. Verify rendering and
login after switching; select the built-in theme if the custom theme fails.
Do not delete the active theme. Restoring a previous custom version may require
restoring the backed-up files and database settings together. This stack does
not download, build or enable a third-party theme automatically.

## Reverse proxy

Configure the independent proxy to join the Compose-managed `xboard` network
(declare it external in the proxy's stack, after this stack creates it). Forward
the panel hostname and **all paths** to `http://xboard:7001`, including the private
admin URL, API, subscriptions, theme assets and `/ws`.

Forward paths without stripping prefixes, preserve `Host`, supply trusted
`X-Forwarded-Proto: https` and client address headers, and support WebSocket
upgrade on `/ws`.

Keep XBoard's internal Caddy enabled: it multiplexes HTTP and `/ws` on port 7001;
it does **not** terminate public TLS. Restrict this Docker network to trusted
services because upstream trusts forwarded proxy headers. A host-based proxy
requires an explicit local port-binding override; there is none by default.

## Persistence and updates

Named volumes store SQLite (`data`), logs (`logs`), installed XBoard themes
(`theme`), plugins (`plugins`) and embedded Redis snapshots (`redis`). Back up
these plus `mount/app.env` (including its stable `APP_KEY`), Compose settings and
retained native theme packages. Stop the service for consistent SQLite backups
or use a proper SQLite backup tool. Treat backups as sensitive.

Before upgrading, back up the database and review upstream changes, then select
`TAG` and run `./upgrade xboard`. Current upstream runs `xboard:update` at boot;
check logs because migration failures may be logged while the container continues
running. Do not assume an image rollback reverses database migrations. For older
images without the current entrypoint, follow that version's upgrade procedure.
The moving `latest` tag is not an immutable pin.

Ordinary `./upgrade -n xboard down` preserves named volumes; `down -v` destroys
them and must not be used as an upgrade procedure.

## Sources and validation scope

Implementation checked against XBoard commit
`e68fec50ef48d86f7666c5ff5e758f2a6e9fa313`:
[deployment](https://github.com/cedar2025/Xboard/blob/e68fec50ef48d86f7666c5ff5e758f2a6e9fa313/docs/en/installation/docker-compose.md),
[image/entrypoint](https://github.com/cedar2025/Xboard/tree/e68fec50ef48d86f7666c5ff5e758f2a6e9fa313/.docker),
[installer](https://github.com/cedar2025/Xboard/blob/e68fec50ef48d86f7666c5ff5e758f2a6e9fa313/app/Console/Commands/XboardInstall.php),
[mounts](https://github.com/cedar2025/Xboard/blob/e68fec50ef48d86f7666c5ff5e758f2a6e9fa313/compose.sample.yaml),
[native theme management](https://github.com/cedar2025/Xboard/blob/e68fec50ef48d86f7666c5ff5e758f2a6e9fa313/app/Services/ThemeService.php)
and [internal HTTP/WebSocket routing](https://github.com/cedar2025/Xboard/blob/e68fec50ef48d86f7666c5ff5e758f2a6e9fa313/.docker/caddy/Caddyfile).

Compose 2.40.3 passed three isolated renders with empty, example and custom
settings through `./upgrade -n xboard config`. Checks covered the single XBoard
service, image settings, persistent mounts, network and absence of published
ports. These were ad hoc static checks, not added to the test suite. The existing
14 repository tests also passed: four GitHub runner configuration tests, seven
PostgreSQL layout/configuration tests and three upgrade-wrapper tests. They do
not test XBoard runtime behavior. No images were pulled or containers started.
Initialization, native theme installation, login/payment, node synchronization
and live proxy/WebSocket behavior require deployment testing.
