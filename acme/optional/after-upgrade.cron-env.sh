#!/usr/bin/env bash

if ${no_up:-} && [ "${docker_args[0]:-}" != 'up' ]; then
  return
fi

# shellcheck disable=SC2016
_docker_compose cp -L .env acme.sh:/.dockerenv
_docker_compose exec -T acme.sh sh -c '
sed -i -E "s|(([0-9*]+ +){5}).*(\"/root/.acme.sh\"/acme.sh)|\1set -o allexport; source /.dockerenv; set +o allexport; \3|" /etc/crontabs/root
'
