ARG IMAGE
FROM ${IMAGE:-atlassian/confluence-server}

ARG UBUNTU_MIRROR

RUN set -ex; \
  if [ -n "${UBUNTU_MIRROR}" ]; then \
    sed -i.bak -E "s|https?://[^/]*/|${UBUNTU_MIRROR}|g" /etc/apt/sources.list; \
  fi; \
  apt-get update; \
  apt-get install -y --no-install-recommends language-selector-common; \
  # All language support
  apt install -y --no-install-recommends $(check-language-support -a | tr ' ' '\n' | grep '^fonts-'); \
  # Enhanced Chinese support
  apt install -y --no-install-recommends 'fonts-arphic-*' 'fonts-cns11643-*'; \
  apt purge -y language-selector-common; \
  rm -rf /var/lib/apt/lists/*; \
  if [ -f /etc/apt/sources.list.bak ]; then \
    mv /etc/apt/sources.list.bak /etc/apt/sources.list; \
  fi
