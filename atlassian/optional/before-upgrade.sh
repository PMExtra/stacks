#!/usr/bin/env bash

# This hook is used to configure external database.
# It will clear the local database dependencies if no local database is configured.

# The file to configure external database
EXTERNAL_DB_FILE=docker-compose.external-database.yml

# List all services that depends on database
SERVICES=(confluence crowd jira)

if [ -f docker-compose.mysql.yml ] || [ -f docker-compose.postgres.yml ]; then
  # Drop the external database configuration if a local database is configured
  rm -f "$EXTERNAL_DB_FILE"
  return
fi

# To append a configuration into EXTERNAL_DB_FILE to clear 'depends_on' field of specified service
# Usage: _remove_dependencies SERVICE_NAME
_remove_dependencies() {
  _service=$1
  if [ -f "docker-compose.$_service.yml" ]; then
    echo "  $_service:" >> "$EXTERNAL_DB_FILE"
    echo "    depends_on: []" >> "$EXTERNAL_DB_FILE"
  fi
}

# Create a new EXTERNAL_DB_FILE
echo "services:" >| "$EXTERNAL_DB_FILE"

# Configure each service that depends on database
for service in "${SERVICES[@]}"; do
  if [ -f "docker-compose.$_service.yml" ]; then
    # Clear 'depends_on' field of the service if the service is enabled
    _remove_dependencies "$service"
  fi
done
