#!/bin/sh

echo "Warning: This stack is deprecated, please use 'openldap' instead."

if _confirm "Would you like to continue use this deprecated stack?" "y"; then
  exit 0
else
  echo "Aborted."
  exit 1
fi
