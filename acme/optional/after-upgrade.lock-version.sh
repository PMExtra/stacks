#!/usr/bin/env bash

if ${no_up:-} && [ "${docker_args[0]:-}" != 'up' ]; then
  return
fi

# shellcheck disable=SC2016
_docker_compose exec -T acme.sh sh -c '
acme.sh --upgrade -b ${ACME_BRANCH:-master} --auto-upgrade 0 --force
'
