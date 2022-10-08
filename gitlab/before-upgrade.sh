#!/usr/bin/env bash

# This hook is used to configure the default component of the stack.

if [ ! -f docker-compose.gitlab.yml ] && [ ! -f docker-compose.runner.yml ]; then
  # Enable GitLab server if no component is enabled
  ln -s optional/docker-compose.gitlab.yml .
fi
