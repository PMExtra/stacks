#!/usr/bin/env bash

# This hook is used to notice security risks.
# It will clear the local database dependencies if no local database is configured.

# $no_up is set from main upgrade script, that indicated if user specify a custom action rather than up
if ${no_up:-} && [ "${docker_args[0]:-}" != 'up' ] && [ "${docker_args[0]:-}" != 'create' ]; then
  # Do nothing if user specify a custom action that won't create or up the stack
  return
fi

# Notice
printf "DPS mounts docker.sock, which can be a potential security risk. Do you want to continue? (y/n) "
read -r _confirm

# It will get an error if the user didn't confirm the action, that will break the main script
expr "$_confirm" : "^[Yy]$" > /dev/null
