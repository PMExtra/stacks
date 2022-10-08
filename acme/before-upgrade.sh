#!/usr/bin/env bash

# This hook is used to fill the environments to avoid unwanted warnings.
# It will create a default '.env' file if not exist.

if [ -f .env ]; then
  # Do nothing if the env file already exists
  return
fi

# Create a default env file
cat > .env << EOF
# Optional alpine repository mirror
ALPINE_MIRROR=

# Optional acme version lock
ACME_BRANCH=
EOF
