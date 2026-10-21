# LiteLLM

This stack follows the official single-service LiteLLM gateway examples. PostgreSQL,
Redis, and a local configuration file are independently selectable Compose components.
Run commands from the repository root through `./upgrade`; no component is enabled by default.

## Environment and models

Create `litellm/.env` with `LITELLM_MASTER_KEY` and `LITELLM_SALT_KEY`. Generate each
value separately with `openssl rand -hex 32`, prefix it with `sk-`, and keep the salt
key unchanged after storing provider credentials in the database. Both values are
required by this stack, including configuration-file deployments.

The image is `docker.litellm.ai/berriai/litellm:${TAG:-latest}`. Set `TAG` to select
another published tag. The default published port is `4000`; `LITELLM_PORT` changes
the host port and `LITELLM_BIND` can supply an address followed by `:`. Neither
variable changes the container's port or health check.

Choose one model configuration mode:

- **Database / Admin UI:** set `DATABASE_URL` for an existing PostgreSQL database,
  or enable the PostgreSQL component below. Set `STORE_MODEL_IN_DB=True` in `.env`
  to manage models through the UI. The UI is at `/ui`; its default username is
  `admin` and its initial password is the master key. Provider credentials can be
  added through the management API or UI; operating this repository does not require a GUI.
- **Configuration file:** enable the config component and provide a real model
  configuration. For operation without a database, omit `DATABASE_URL` and
  `STORE_MODEL_IN_DB` entirely. Basic model forwarding works without PostgreSQL;
  database-backed virtual keys, users/teams, persistent spend tracking, database
  budgets, and Admin UI management require PostgreSQL. Redis does not replace it.

A base Compose configuration can validate without a database or a model list;
that alone does not make a usable gateway. Configure one of the modes above.

## Existing PostgreSQL

Do not enable `compose.postgres.yaml`. Put the complete connection URI in `.env`:

```dotenv
DATABASE_URL='postgresql://litellm:p%40ss%3Aword%2F%25%24%23@db.example.net:5432/litellm'
STORE_MODEL_IN_DB=True
```

The illustrative password in this URI decodes to `p@ss:word/%$#`; replace the host
and credentials. Percent-encode URI username/password components, not the entire
URI. Add connection query parameters such as `sslmode` only as required by your
existing database. The endpoint must be reachable from the container; `localhost`
inside the container is not the Docker host. Database initialization/migrations
retain the official image's behavior; supply a database account with the permissions
LiteLLM needs. This stack does not provision or migrate an external database separately.

## Optional local PostgreSQL

```sh
ln -s optional/compose.postgres.yaml litellm/compose.postgres.yaml
```

Set both values in `litellm/.env`:

```dotenv
POSTGRES_PASSWORD='p@ss:word/%$#'
POSTGRES_PASSWORD_URLENCODED='p%40ss%3Aword%2F%25%24%23'
STORE_MODEL_IN_DB=True
```

These are illustrative credentials, not defaults. `POSTGRES_PASSWORD` is passed
unchanged to PostgreSQL. `POSTGRES_PASSWORD_URLENCODED` must be the percent-encoded
form of that exact password. Generate it interactively without putting the raw
password in a shell command:

```sh
python3 -c 'import getpass, urllib.parse; print(urllib.parse.quote(getpass.getpass("PostgreSQL password: "), safe=""))'
```

Compose cannot URL-encode a value or verify the two values match. Both are required;
there is deliberately no unsafe fallback to the raw password. Use Compose dotenv
single-quoted values for literal `$` characters; see the official dotenv syntax for
escaping a literal single quote. An encoded password is still a credential.

This component fixes the database/user to `litellm`, overrides the application's
`DATABASE_URL` to use `postgres:5432`, and waits for PostgreSQL's health check. Its
`postgres:16` data lives in `postgres_data` at `/var/lib/postgresql/data`. There is
no database host port. Changing `.env` does not change passwords in an already
initialized PostgreSQL volume; update the database credentials separately.

## Optional configuration file

```sh
mkdir -p litellm/mount
ln -s optional/compose.config.yaml litellm/compose.config.yaml
```

Create `litellm/mount/config.yaml` before starting; the bind mount does not create a
missing source as a directory. For example, for an OpenAI-compatible provider:

```yaml
model_list:
  - model_name: upstream
    litellm_params:
      model: os.environ/LITELLM_MODEL
      api_base: os.environ/UPSTREAM_API_BASE
      api_key: os.environ/UPSTREAM_API_KEY
```

Set `LITELLM_MODEL` to `openai/` followed by the provider's actual model ID,
`UPSTREAM_API_BASE` to its API base URL, and `UPSTREAM_API_KEY` to its credential in
`.env`. Clients then request the alias `upstream`. These are deployment inputs, not
working credentials or a built-in model. The same file can hold Redis settings below.

## Redis: connection versus functionality

A local Redis container is optional even when Redis functionality is needed: use an
existing endpoint instead. One worker can run basic forwarding without Redis. Multiple
workers (including workers in one container) need shared state for consistent rate
limits, budget coordination, routing cooldowns, and invalidations. Without Redis these
features can be local to each worker or degraded. Response caching and the Redis spend
transaction buffer are separate opt-in features; this stack enables neither automatically.

For an existing standalone Redis, leave the Redis component disabled and set
`REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD` in `.env`. Use an empty password for
an endpoint without authentication. For local Redis:

```sh
ln -s optional/compose.redis.yaml litellm/compose.redis.yaml
```

The component sets `REDIS_HOST=redis`, `REDIS_PORT=6379`, and uses the optional
`REDIS_PASSWORD` for both server authentication and the client. Password text is passed
as a command argument without a shell; an empty password disables authentication. It adds
no host port, persistent volume, AOF, snapshot tuning, or resource settings.

**When using local Redis, remove external Redis settings from `.env` and your shell**:
`REDIS_URL`, `REDIS_USERNAME`, `REDIS_SSL`, `REDIS_DB`, cluster/sentinel variables, and
other external endpoint options. The component overrides only host, port and password;
other values from `env_file` remain present. Mixing a URL or external topology with the
local component is unsupported and can select the wrong endpoint or fail to connect.

To explicitly use Redis for coordination and router state without enabling response
caching, enable the config component and add:

```yaml
general_settings:
  coordination_redis:
    host: os.environ/REDIS_HOST
    port: os.environ/REDIS_PORT
    password: os.environ/REDIS_PASSWORD
router_settings:
  redis_host: os.environ/REDIS_HOST
  redis_port: os.environ/REDIS_PORT
  redis_password: os.environ/REDIS_PASSWORD
```

Set all three referenced variables, including `REDIS_PASSWORD=''` when using an
unauthenticated external endpoint. For an existing Redis URL (including TLS), use
`REDIS_URL` with `general_settings.coordination_redis.url: os.environ/REDIS_URL` and
`router_settings.redis_url: os.environ/REDIS_URL` instead of the host/port/password
blocks. Do not combine the URL example with the local Redis component.

Only if response caching is desired, also add:

```yaml
litellm_settings:
  cache: true
  cache_params:
    type: redis
    host: os.environ/REDIS_HOST
    port: os.environ/REDIS_PORT
    password: os.environ/REDIS_PASSWORD
```

For a URL-based external connection, replace those three cache connection fields
with `url: os.environ/REDIS_URL`. Merely starting Redis does not enable response
caching. Official documentation and current main differ on bare `REDIS_*` behavior:
main has a best-effort coordination fallback, but this is not a promise that routing
and response caching are configured. Use explicit settings and check that your chosen
image tag supports them, especially `general_settings.coordination_redis`.

## Variable precedence and validation

Compose reads `.env` for interpolation; `env_file: .env` also passes its values into
the LiteLLM container. Explicit `environment` entries override `env_file`, and shell
variables take precedence over `.env` for `${...}` interpolation. Consequently:

- Master/salt keys and local dependency credentials can be overridden by shell values.
- The PostgreSQL component overrides an external `DATABASE_URL` from `.env`.
- The Redis component overrides host, port and password from `.env`, but not other
  Redis settings. Remove conflicting external settings as described above.
- Shell-only `DATABASE_URL`, `STORE_MODEL_IN_DB`, provider credentials or external
  Redis settings are not automatically forwarded: put them in `litellm/.env`.
- Keep connection settings out of `config.yaml` when the environment/component should
  control them; use `os.environ/...` references. Do not additionally set a competing
  `general_settings.database_url` or literal Redis endpoint in that file.

Validate the selected configuration without pulling images or starting containers:

```sh
./upgrade -n litellm config --quiet
```

Use `./upgrade litellm` only when you intend to deploy. Optional components are enabled
by the stack-local symlinks above; remove a link to exclude that component from future
Compose merges. Removing a link alone does not stop an already running container.
The existing repository ignore rules exclude `.env`, `mount/`, and component symlinks.
Do not share rendered `config` output: it includes credentials.

## Upstream basis

Reviewed upstream commit: `b6f91a221b6b9df6f8a89ec6f8264ac87d63ff5d`.

- [Official Quickstart Compose](https://github.com/BerriAI/litellm/blob/b6f91a221b6b9df6f8a89ec6f8264ac87d63ff5d/docker/docker-compose.quickstart.yml)
- [Official root Compose and health check](https://github.com/BerriAI/litellm/blob/b6f91a221b6b9df6f8a89ec6f8264ac87d63ff5d/docker-compose.yml)
- [Quickstart](https://docs.litellm.ai/docs/proxy/docker_quick_start), [virtual keys](https://docs.litellm.ai/docs/proxy/virtual_keys), [CLI configuration](https://docs.litellm.ai/docs/proxy/quick_start)
- [Redis requirements](https://docs.litellm.ai/docs/proxy/redis_requirements), [Redis configuration](https://docs.litellm.ai/docs/proxy/caching_redis)
- [Coordination initialization and environment fallback](https://github.com/BerriAI/litellm/blob/b6f91a221b6b9df6f8a89ec6f8264ac87d63ff5d/litellm/proxy/proxy_server.py#L6109)
- [Compose interpolation and dotenv syntax](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)

Compared with upstream, local source builds and Prometheus are omitted. PostgreSQL
and config-file wiring are optional; database model storage is selected through `.env`.
The root example's fixed container/volume names and database host port are unnecessary
here. Redis uses the repository's `sub2api` image choice without copying its persistence
tuning. No proxy, custom network, resource limit, migration job, or hardening layer is added.
