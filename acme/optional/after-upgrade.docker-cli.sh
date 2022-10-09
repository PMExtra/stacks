#!/usr/bin/env bash

if ${no_up:-} && [ "${docker_args[0]:-}" != 'up' ]; then
  return
fi

# shellcheck disable=SC2016
_docker_compose exec -T acme.sh sh -c '
set -e
cp -n /etc/apk/repositories /etc/apk/repositories.bak || true
if [ -n "${ALPINE_MIRROR}" ]; then
  sed -i -E "s|https?://[^/]*/|${ALPINE_MIRROR}|g" /etc/apk/repositories
fi
apk update
apk add docker-cli
'
