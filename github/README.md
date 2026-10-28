# GitHub Actions runner

This stack provides one persistent self-hosted runner for trusted development
workflows. The base `compose.yaml` only names the Compose-managed `github`
network; the optional runner is enabled locally. Operate the stack from the
repository root through `./upgrade`.

## Why a community image?

GitHub **does** publish `ghcr.io/actions/actions-runner`, and its maintainers
explicitly support standalone use as well as ARC. It is a minimal base image:
there is no default runner `ENTRYPOINT`/`CMD`, registration writes configuration
alongside the runner program, and standalone Compose users must supply startup,
registration and persistence handling themselves. This is a packaging limitation,
not a claim that GitHub does not support Docker or that standalone operation is
impossible. See the [official image announcement](https://github.com/actions/runner/issues/367#issuecomment-1362881910),
[entrypoint explanation](https://github.com/actions/runner/issues/367#issuecomment-1375386101),
[current Dockerfile](https://github.com/actions/runner/blob/main/images/Dockerfile)
and [standalone documentation request #4456](https://github.com/actions/runner/issues/4456).

[myoung34/github-runner](https://github.com/myoung34/docker-github-actions-runner)
wraps the official runner with registration, startup and configuration reuse.
Its existing `CONFIGURED_ACTIONS_RUNNER_FILES_DIR` support lets us keep identity
in a named volume without maintaining our own image or entrypoint. We accept an
additional third-party supply-chain dependency: review upstream changes and use
a reviewed published version tag via `TAG` for controlled upgrades. `latest`
is the repository fallback; the example's `ubuntu-noble` selects a distribution,
**not an immutable version**. Both moving and version tags may be republished;
for digest pinning, use an ignored local Compose override of `image`.

A read-only manifest check on 2026-10-28 confirmed `ubuntu-noble` includes
`linux/amd64` and `linux/arm64`. No `platform` is forced. Recheck the manifest
when selecting another tag. This image is not GitHub's hosted runner environment
with its complete tool collection; workflows must prepare their required tools.

## Configure and enable

```sh
cp github/.env.example github/.env
chmod 600 github/.env
ln -s optional/compose.runner.yaml github/compose.runner.yaml
```

Edit the ignored `github/.env` before starting:

| Setting | Repository runner | Organization runner |
| --- | --- | --- |
| `RUNNER_SCOPE` | `repo` | `org` |
| Target | `REPO_URL=https://github.com/OWNER/REPO` | `ORG_NAME=organization-login` |
| `RUNNER_NAME` | A unique, stable name | A unique, stable name |
| `RUNNER_TOKEN` | Repository registration token | Organization registration token |

Leave the unused target empty. Use exactly `repo` or `org`; upstream treats
unrecognized scope values as repository scope. Compose validates the required
nonempty name; upstream validates the selected target during startup. Compose
`config` does not validate target existence, scope permissions or token validity.
For organization runners, restrict accessible repositories through GitHub runner
groups; `RUNNER_GROUP` can be added to `.env` if needed.

Obtain a short-lived **registration token** for the selected repository or
organization just before first start (using GitHub's registration instructions
or the corresponding API). Do not use a workflow `GITHUB_TOKEN` in its place.
No permanent PAT is required. If initial registration fails because the token
expired, replace it with a fresh registration token before retrying.

```sh
./upgrade -n github config --quiet
./upgrade github
./upgrade -n github logs --tail=100 runner
```

Check that GitHub reports the intended runner online. After successful
registration, clear/remove `RUNNER_TOKEN` in `.env` and recreate the container
after any job finishes, so the old token is removed from its container metadata:

```sh
./upgrade -n github up -d --force-recreate runner
```

The registration token's expiry does not expire the registered runner identity.
An existing `runner_config` volume restores that identity on restart/recreation,
so Compose intentionally allows an empty/missing token. An empty configuration
volume still needs a fresh token. Configuration output can contain secrets:
prefer `config --quiet`, and do not publish rendered output or debug logs.

Without the local symlink, `./upgrade -n github config` renders `services: {}`
with Compose 2.40.3. This is expected for the network-only base; no runner is
enabled and the unused network is omitted from the rendered configuration. The symlink and `.env` stay local and ignored by Git.

## Proxy and development network

Set lowercase `http_proxy` and `https_proxy` in `.env` to an HTTP proxy reachable
from the container, for example `http://proxy.example.test:3128`. An HTTP CONNECT
proxy still uses an `http://` URL for `https_proxy`. Leave them empty for direct
access. The runner does not directly support a SOCKS proxy; provide an HTTP
proxy endpoint if the upstream connection is SOCKS. See GitHub's
[runner proxy documentation](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/use-proxy-servers).

Set `no_proxy` to comma-separated internal service/database hostnames that must
be reached directly. GitHub's runner supports hostname exclusions, not IP-based
exclusions; other job tools may interpret this variable differently. The example
includes loopback for tools that support it. Do not exempt GitHub if direct
access is blocked. `localhost` inside the container is the container itself,
not the host's proxy or database. Ensure routing, DNS and firewall rules allow
the runner to reach the development database; this stack creates only its own
`github` network and does not automatically join a database's network.

These variables cover runner/job traffic, **not image pulls**: registry proxy or
mirror settings belong to the Docker daemon and remain separately configured.
Some workflow tools require their own proxy settings. Do not commit actual proxy
addresses, passwords or database credentials. Supply database credentials through
workflow secrets using a limited development-database account.

## Persistence, jobs and lifecycle

- `github_runner` is one container with one registration identity. Do not scale
  it or share its configuration volume between runners. Choose a unique name:
  upstream registration uses `--replace`, so a duplicate name can replace an
  existing registration.
- `github_runner_config` stores identity/configuration, including credentials;
  `github_runner_work` stores the work directory. Protect backups and volume
  access. Work-directory persistence does not make a clean sandbox between jobs.
- `RUN_AS_ROOT=false` runs the listener/jobs as the runner user, but the image
  entrypoint still initializes as root and the runner user has sudo. This is not
  a security isolation boundary. `UNSET_CONFIG_VARS=true` reduces configuration
  variables inherited by jobs; it does not protect credentials from malicious
  jobs with filesystem/sudo access. Run only trusted workflows and actions;
  do not execute untrusted fork pull requests here.
- The default supports shell steps and JavaScript actions. There is no Docker
  socket, privileged mode, DinD, published port or synthetic healthcheck.
  Container actions, job `container:` and `services:` need a separate Docker
  design (daemon access, permissions, shared paths and networking); mounting a
  socket alone is not a complete solution. Confirm readiness in GitHub and logs.
- Official runner automatic updates stay enabled. Do not add `EPHEMERAL=false`
  or `DISABLE_AUTO_UPDATE=false`: upstream enables these options for **any
  nonempty string**, including `false`. Leave them absent for this persistent
  runner. Updating the image refreshes the base OS/tools; pinning its tag does
  not freeze the runner's own automatic updates.

Before upgrades or recreation, prevent new jobs from targeting this runner and
wait for the current job to finish. Then run `./upgrade github` to pull the
selected tag and recreate as needed. Changing the target, name or registration
settings in `.env` does not reconfigure an already persisted identity: stop the
runner, remove the old GitHub registration, and deliberately reset its config
volume before registering again with a fresh token. Never delete the working
volume as an incidental part of an upgrade.

`./upgrade -n github stop runner` stops the process without deregistering it
(`DISABLE_AUTOMATIC_DEREGISTRATION=true`). For final retirement, stop it, manually
remove its registration in the repository/organization Actions runner settings
(or API), then use `./upgrade -n github down`. Named volumes survive `down`;
only use `./upgrade -n github down -v` when intentionally discarding both
configuration credentials and all stored work. Removing GitHub registration
without clearing stale config will not make the next start register afresh.

## Validation

`python3 -B -m unittest discover -s tests -v` includes isolated Compose checks
through `./upgrade -n github config`: optional activation, required name,
repo/org configurations, empty/missing/dummy token, tag/proxy propagation,
persistent mounts and the absence of Docker access/ports/privileged settings.
These are static checks only: no images are pulled, no runner is registered,
and no jobs, live persistence recovery or database connections are exercised.
