#!/usr/bin/env bash

if ${no_up:-} && [ "${docker_args[0]:-}" != 'up' ]; then
  return
fi

# shellcheck disable=SC2016
_docker_compose cp -L .env acme.sh:/.dockerenv
_docker_compose exec -T acme.sh sh -c '
grep -qF "set -o allexport" /.dockerenv || \
  sed -i "1i set -o allexport" /.dockerenv; \
grep -qF "set +o allexport" /.dockerenv || \
  sed -i "\$a set +o allexport" /.dockerenv; \
grep -qF "source /.dockerenv;" /etc/crontabs/root || \
  sed -i -E "s|(([0-9*]+ +){5}) *(.*/acme.sh)|\1source /.dockerenv; \3|" /etc/crontabs/root
'
