# GitLab SSH Setup

Initial setup. Run host commands as root. UID/GID 2222 must be available on both the host and in the container.

## 1. Create the host git user and home directory

```bash
groupadd -g 2222 git
useradd -u 2222 -g 2222 -d /var/opt/gitlab -m -s /bin/sh git
```

## 2. Generate the host-to-container SSH key

```bash
install -d -m 700 -o git -g git /var/opt/gitlab/.ssh
sudo -u git ssh-keygen -t ed25519 \
  -f /var/opt/gitlab/.ssh/gitlab_trampoline \
  -N ''
```

## 3. Configure matching UID/GID in gitlab.rb

```ruby
user['uid'] = 2222
user['gid'] = 2222
manage_accounts['enable'] = true
```

## 4. Install the host gitlab-shell wrapper

```bash
install -d -m 755 /opt/gitlab/embedded/service/gitlab-shell/bin

cat >/opt/gitlab/embedded/service/gitlab-shell/bin/gitlab-shell <<'EOF'
#!/bin/sh
exec ssh \
  -o BatchMode=yes \
  -o IdentitiesOnly=yes \
  -o StrictHostKeyChecking=accept-new \
  -i /var/opt/gitlab/.ssh/gitlab_trampoline \
  -p 2222 git@127.0.0.1 \
  "SSH_ORIGINAL_COMMAND=$(env printf "%q" "$SSH_ORIGINAL_COMMAND")" \
  "$0" "$@"
EOF

chmod 755 /opt/gitlab/embedded/service/gitlab-shell/bin/gitlab-shell
```

## 5. Restrict host SSH access for the git user

Append this block once, at the end of the host's sshd_config.

```bash
cat >>/etc/ssh/sshd_config <<'EOF'
Match User git
    PasswordAuthentication no
    KbdInteractiveAuthentication no
    X11Forwarding no
    AllowAgentForwarding no
    AllowTcpForwarding no
    AllowStreamLocalForwarding no
    PermitTunnel no
    PermitTTY no
EOF

/usr/sbin/sshd -t && systemctl reload ssh
```

## 6. Configure the Compose service

Merge these settings into the existing GitLab service. Keep the container SSH configuration that reads `/gitlab-data/ssh/authorized_keys`.

```yaml
services:
  gitlab:
    ports:
      - "127.0.0.1:2222:22"
    volumes:
      - /var/opt/gitlab/.ssh:/var/opt/gitlab/.ssh
      - /var/opt/gitlab/.ssh/gitlab_trampoline.pub:/gitlab-data/ssh/authorized_keys:ro
```
