#!/usr/bin/env bash

if [ -f compose.data.yaml ] || [ -f compose.data_legacy.yaml ]; then
  return
fi

cat >&2 <<'EOF'
Choose a PostgreSQL data layout by enabling one of these configurations:
  ln -s optional/compose.data.yaml ./
  ln -s optional/compose.data_legacy.yaml ./
EOF
exit 1
