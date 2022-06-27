#!/usr/bin/env bash

if [ ! -f docker-compose.gitlab.yml ] && [ ! -f docker-compose.runner.yml ]; then
  ln -s optional/docker-compose.gitlab.yml .
fi
