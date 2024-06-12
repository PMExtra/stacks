#!/usr/bin/env bash

# This hook is used to fill the environments to avoid unwanted warnings.
# It will create a default '.env' file if not exist.

if [ -f .env ]; then
  if [ ! -f after-upgrade.cron-env.sh ] && [ ! -f .no-cron-env.flag ] && [ "$(grep -c '^\s*[^#]' .env)" -gt 3 ]; then
    if _confirm 'Do you want the patch to load environment variables for cron jobs?' 'y'; then
      ln -s optional/after-upgrade.cron-env.sh ./
    else
      echo 'Keep this file to prevent the loading env for cron jobs confirmation.' >|.no-cron-env.flag
    fi
  fi
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
