#!/usr/bin/env bash

# This hook is used to configure the default component of the stack.

if [ ! -f docker-compose.portainer.yml ] && [ ! -f docker-compose.agent.yml ]; then
  # Enable both of server and agent if no component is enabled
  ln -s optional/docker-compose.*.yml .
fi
