#!/usr/bin/env bash

# This hook is used to fill the environments to avoid unwanted warnings.
# It will create a default '.db.env' file if not exist.

DB_ENV_FILE=.db.env

if [ -f .env ]; then
  eval "$(grep "^DB_ENV_FILE=" .env)"
fi

if [ -f "$DB_ENV_FILE" ]; then
  return
fi

# Create a default env file
cat > "$DB_ENV_FILE" << EOF
# Type of database (mysql, postgres, mariadb, mssql or sqlite)
DB_TYPE=sqlite

# For PostgreSQL, MySQL, MariaDB and MSSQL only:
# Hostname or IP of the database
DB_HOST=
# Port of the database
DB_PORT=
# Username to connect to the database
DB_USER=
# Password to connect to the database
DB_PASS=
# Database name
DB_NAME=

# When connecting to a database server with SSL enforced:
# Set to either 1 or true to enable. (optional, off if omitted)
DB_SSL=
# Database CA certificate content, as a single line string (without spaces or new lines), without the prefix and suffix lines. (optional, requires 2.3+)
DB_SSL_CA=

# Alternative way to provide the database password, via a local file secret:
# Path to the mapped file containing to the database password. (optional, replaces DB_PASS)
DB_PASS_FILE=

# For SQLite only:
# Path to the SQLite file
DB_FILEPATH=data/db.sqlite
EOF
