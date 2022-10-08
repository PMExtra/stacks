#!/usr/bin/env bash

# This hook is used to fill the environments to avoid unwanted warnings.
# It will create a default '.env' file if not exist.

if [ -f .env ]; then
  # Do nothing if the env file already exists
  return
fi

# Create a default env file
cat > .env << EOF
# Sync Interval (seconds)
PVTZ_SYNC_INTERVAL=60

# Aliyun Access Token
PVTZ_SYNC_ACCESS_KEY=
PVTZ_SYNC_SECRET_KEY=

# Working Region
PVTZ_SYNC_REGION_ID=

# Private Zone Domain
PVTZ_SYNC_PVTZ_DOMAIN=
PVTZ_SYNC_PVTZ_RESOURCE_GROUP_ID=

# ECS List Filter
PVTZ_SYNC_ECS_ZONE_ID=
PVTZ_SYNC_ECS_VPC_ID=
PVTZ_SYNC_ECS_VSWITCH_ID=
PVTZ_SYNC_ECS_SECURITY_GROUP_ID=
PVTZ_SYNC_ECS_RESOURCE_GROUP_ID=
# Multiple Ids Split By Space
PVTZ_SYNC_ECS_INSTANCE_IDS=
PVTZ_SYNC_ECS_EXCLUDE_INSTANCE_IDS=

# Optional Advanced Options
PVTZ_SYNC_REQUEST_NETWORK=
PVTZ_SYNC_ECS_REGION_ID=
PVTZ_SYNC_PVTZ_REGION_ID=
PVTZ_SYNC_REMARK=
EOF
