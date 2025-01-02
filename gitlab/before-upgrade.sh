#!/usr/bin/env bash

# This hook is used to configure the default component of the stack.

if ! compgen -G "compose.*.yaml" > /dev/null; then
  # Enable GitLab server if no component is enabled
  ln -s optional/compose.gitlab.yaml ./
fi
