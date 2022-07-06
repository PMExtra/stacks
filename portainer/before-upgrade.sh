#!/usr/bin/env bash

if [ ! -f docker-compose.portainer.yml ] && [ ! -f docker-compose.agent.yml ]; then
  ln -s optional/docker-compose.*.yml .
fi
