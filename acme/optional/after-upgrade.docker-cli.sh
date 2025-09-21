#!/usr/bin/env bash

if ${no_up:-} && [ "${docker_args[0]:-}" != 'up' ]; then
  return
fi

# shellcheck disable=SC2016
_docker_compose exec -T acme.sh sh -c '
if [ -n "${ALPINE_MIRROR:-}" ]; then
  sed -i.bak -E "s|https?://[^/]*/|${ALPINE_MIRROR}|g" /etc/apk/repositories
fi
apk update && apk add docker-cli
'
