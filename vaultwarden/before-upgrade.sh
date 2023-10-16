#!/usr/bin/env sh

# This hook is used to fill the environments to avoid unwanted warnings.
# It will create a default '.env' file if not exist.

if [ -f .env.template ]; then
  # Do nothing if the env file already exists
  return
fi

_exists() {
  cmd="$1"
  if eval type type >/dev/null 2>&1; then
    eval type "$cmd" >/dev/null 2>&1
  elif command >/dev/null 2>&1; then
    command -v "$cmd" >/dev/null 2>&1
  else
    which "$cmd" >/dev/null 2>&1
  fi
  ret="$?"
  return $ret
}

# Create a default env file
_ENV_TEMPLATE_URL=https://raw.githubusercontent.com/dani-garcia/vaultwarden/main/.env.template
(_exists curl && curl -fsSL -o .env.template "${_ENV_TEMPLATE_URL}") \
|| (_exists wget && wget -q -O .env.template "${_ENV_TEMPLATE_URL}") \
|| echo "Failed to download the .env template from \"${_ENV_TEMPLATE_URL}\"."

if [ -f .env ]; then
  return
fi

if [ ! -f .env.template ]; then
  echo 'Please create the .env file mannually.'
  return 1
fi

cp .env.template .env
