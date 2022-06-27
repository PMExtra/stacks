#!/usr/bin/env bash

if [ -f .env ]; then
  return
fi

cat > .env << EOF
# Optional alpine repository mirror
ALPINE_MIRROR=

# Optional acme version lock
ACME_BRANCH=
EOF
