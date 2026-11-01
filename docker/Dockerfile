FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl wget gnupg git git-lfs openssh-client ripgrep fd-find jq \
      python3 python3-pip python3-venv build-essential pkg-config \
      tini tmux less procps psmisc unzip zip xz-utils file nano \
      inotify-tools gh tzdata locales \
 && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && sed -i 's/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen \
 && locale-gen \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 agent \
 && useradd -m -u 1000 -g 1000 -s /bin/bash agent

COPY bin/ /opt/t3a/
COPY docker/entrypoint /opt/t3a/entrypoint
RUN chmod 0755 /opt/t3a/*

ENV HOME=/home/agent \
    LANG=en_US.UTF-8 \
    NPM_CONFIG_PREFIX=/home/agent/.npm-global \
    PATH=/home/agent/.local/bin:/home/agent/.npm-global/bin:/opt/t3a:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

USER agent
WORKDIR /workspace
EXPOSE 3773
ENTRYPOINT ["/usr/bin/tini", "--", "/opt/t3a/entrypoint"]
