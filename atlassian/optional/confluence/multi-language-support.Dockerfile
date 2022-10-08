ARG IMAGE
FROM ${IMAGE:-atlassian/confluence-server}

ARG UBUNTU_MIRROR

RUN set -ex; \
  if [ -n "${UBUNTU_MIRROR}" ]; then \
    sed -i.bak -E "s|https?://[^/]*/|${UBUNTU_MIRROR}|g" /etc/apt/sources.list; \
  fi; \
  apt-get update; \
  apt-get install -y --no-install-recommends language-selector-common; \
  apt install -y --no-install-recommends $(check-language-support -a | tr ' ' '\n' | grep '^fonts-'); \
  fc-cache -f -v; \
  apt purge -y language-selector-common; \
  rm -rf /var/lib/apt/lists/*; \
  if [ -f /etc/apt/sources.list.bak ]; then \
    mv /etc/apt/sources.list.bak /etc/apt/sources.list; \
  fi
