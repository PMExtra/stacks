ARG TAG=latest
FROM postgres:${TAG}

ARG DEBIAN_MIRROR
ARG POSTGRESQL_PUB_MIRROR
ARG INSTALL_PACKAGES

RUN set -ex; \
  if [ -z "${INSTALL_PACKAGES}" ]; then \
    exit; \
  fi; \
  if [ -n "${DEBIAN_MIRROR}" ]; then \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i.bak -E "s|https?://[^/]+|${DEBIAN_MIRROR%/}|" /etc/apt/sources.list.d/debian.sources; \
    else \
      sed -i.bak -E "s|https?://[^/]+|${DEBIAN_MIRROR%/}|" /etc/apt/sources.list; \
    fi; \
  fi; \
  if [ -n "${POSTGRESQL_PUB_MIRROR}" ]; then \
    sed -i.bak -E "s|https?://[^/]+/(pub/)?|${POSTGRESQL_PUB_MIRROR%/}/|" /etc/apt/sources.list.d/pgdg.list; \
  fi; \
  apt-get update; \
  if [ -n "${INSTALL_PACKAGES}" ]; then \
    apt-get install -y --no-install-recommends \
      $(echo "${INSTALL_PACKAGES}" | xargs -n 1 printf -- "postgresql-%d-%s " ${PG_MAJOR}); \
  fi; \
  rm -rf /var/lib/apt/lists/*; \
  if [ -f /etc/apt/sources.list.bak ]; then \
    mv /etc/apt/sources.list.bak /etc/apt/sources.list; \
  fi; \
  if [ -f /etc/apt/sources.list.d/pgdg.list.bak ]; then \
    mv /etc/apt/sources.list.d/pgdg.list.bak /etc/apt/sources.list.d/pgdg.list; \
  fi
