# Stack regression tests

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

`support.py` provides the shared temporary stack and recording Docker stub;
tests do not instantiate other test cases or call their setup methods manually.

The PostgreSQL hook tests verify that a missing data-layout choice blocks both
the default upgrade and custom `config`/`down` commands before any Docker action,
without creating a layout file. Data-only, legacy-only and both layouts each
exercise one successful command; repeating every command for every valid layout
adds no distinct hook behavior.

Configuration tests require Docker Compose and parse temporary copies with a
controlled environment. They protect project-specific contracts:

- PostgreSQL's explicit nonempty `TAG` requirement in both base and local-build
  configurations; one representative explicit tag checks image selection and
  the build argument. Multiple ordinary tag strings need no separate matrix.
- All four layout combinations, including volume identity, mount targets and
  legacy `PGDATA`. The base configuration intentionally has no data mount.
- sub2api's PostgreSQL 18 parent mount and separate persistent volume, plus its
  ability to use an external database without the standalone PostgreSQL gate.

No images are pulled, containers started or existing data volumes accessed.
Other stacks and hooks are not covered by this suite. Routine interpolation
changes can be checked with temporary `config` runs; the RedApp PUBLIC_URL change
used those checks and added no persistent test. Add maintained tests for project
behavior or safety boundaries, rather than Compose or shell semantics alone.
