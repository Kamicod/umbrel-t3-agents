FROM node:22-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl wget git git-lfs openssh-client ripgrep fd-find jq \
      python3 python3-pip python3-venv build-essential pkg-config \
      tini tmux less procps psmisc unzip zip xz-utils file nano \
      inotify-tools gh tzdata locales openssh-server \
 && sed -i 's/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen \
 && locale-gen \
 && rm -f /etc/ssh/ssh_host_* \
 && mkdir -p /run/sshd \
 && rm -rf /var/lib/apt/lists/*

COPY bin/ /opt/t3a/
COPY docker/entrypoint /opt/t3a/entrypoint
RUN chmod 0755 /opt/t3a/*

ENV HOME=/home/node \
    LANG=en_US.UTF-8 \
    NPM_CONFIG_PREFIX=/home/node/.npm-global \
    PATH=/home/node/.local/bin:/home/node/.npm-global/bin:/opt/t3a:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

USER node
WORKDIR /workspace
EXPOSE 3773 22
ENTRYPOINT ["/usr/bin/tini", "--", "/opt/t3a/entrypoint"]
