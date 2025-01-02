#!/usr/bin/env bash

# This hook is used to smoothly transition expose ports from default to optional configuration.

if [ -f compose.expose.yaml ] || [ -f .no-expose.flag ]; then
  # Do nothing if the env file already exists
  return
fi

if _confirm "The exposed ports 80 and 443 has been moved to an optional compose file.\nDo you want to enable it?" "y"; then
  ln -s optional/compose.expose.yaml ./
else
  echo "Keep this file to prevent the exposing ports confirmation." >> .no-expose.flag
fi
