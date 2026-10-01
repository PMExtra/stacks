# Upgrade CLI regression tests

From the repository root:

```sh
python3 -B -m unittest discover -s tests -v
bash -n upgrade postgres/before-upgrade.sh
git diff --check
```

The CLI tests use temporary directories and a stub Docker executable. They cover
preservation of repeated `--hook-args`/`-a` values
(including spaces), rejection of missing values, and forwarding of ordinary
Compose arguments. Hooks can read the values from the `hook_args` Bash array.

The data-layout tests cover absent, data-only, legacy-only and both configurations
for the standalone PostgreSQL hook. Configuration tests require Docker Compose
and parse temporary copies to check volume names, mount targets and PGDATA,
including sub2api's PostgreSQL 18 mount and external-database configuration.
No images are
pulled, containers started or existing data volumes accessed.
