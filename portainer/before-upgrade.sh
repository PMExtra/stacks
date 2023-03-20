#!/usr/bin/env bash

# This hook is used to configure the default component of the stack.

if ! compgen -G "docker-compose.*.yml" > /dev/null; then
  # Enable both of server and agent if no component is enabled
  ln -s optional/docker-compose.portainer.yml .
  ln -s optional/docker-compose.local-agent.yml .
fi
