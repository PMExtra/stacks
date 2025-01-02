#!/usr/bin/env bash

# This hook is used to configure the default component of the stack.

if ! compgen -G "compose.*.yaml" > /dev/null; then
  # Enable both of server and agent if no component is enabled
  ln -s optional/compose.portainer.yaml ./
  ln -s optional/compose.local-agent.yaml ./
fi
