# PostgreSQL

Set `TAG` explicitly in `postgres/.env` before operating this stack, for example:

```dotenv
TAG=18
```

Compose rejects an unset or empty `TAG`, including with the optional local build.
Any explicit tag is accepted, including `latest`; choose a version compatible
with your data and plan major-version migrations yourself. This stack makes an
exception to the repository's default `latest` policy to avoid accidental
PostgreSQL major-version upgrades.

Select the data layout appropriate to that version before using `./upgrade`:

```sh
# PostgreSQL 18+ parent-directory mount:
ln -s optional/compose.data.yaml postgres/compose.data.yaml
# Or the legacy data-directory mount for older versions:
ln -s optional/compose.data_legacy.yaml postgres/compose.data_legacy.yaml
```

Enable the appropriate layout rather than running both example commands.
Provide the required PostgreSQL authentication settings in `postgres/.env`, then
validate from the repository root:

```sh
./upgrade --no-up postgres config --quiet
```
