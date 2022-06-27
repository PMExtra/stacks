#!/usr/bin/env bash

if ${no_up:-} && [ "${1}" != 'up' ]; then
  return
fi

printf "DPS mounts docker.sock, which can be a potential security risk. Do you want to continue? (y/n) "
read -r _confirm
expr "$_confirm" : "^[Yy]$" > /dev/null
