#!/usr/bin/env bash

# This hook is used to configure the default component of the stack.

if ! compgen -G "docker-compose.*.yml" > /dev/null; then
  # Enable GitLab server if no component is enabled
  ln -s optional/docker-compose.gitlab.yml .
fi
