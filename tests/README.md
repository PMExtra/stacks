# Upgrade CLI regression tests

From the repository root:

```sh
python3 -B -m unittest discover -s tests -v
bash -n upgrade
git diff --check
```

The tests use temporary directories and a stub Docker executable; no containers
are started. They cover preservation of repeated `--hook-args`/`-a` values
(including spaces), rejection of missing values, and forwarding of ordinary
Compose arguments. Hooks can read the values from the `hook_args` Bash array.
