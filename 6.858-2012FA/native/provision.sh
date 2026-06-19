#!/bin/bash
# Provision packages inside the Lima mit6858 VM (after first boot).
set -eux
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  gcc gcc-multilib g++-multilib make libssl-dev execstack strace \
  curl wget python3 python-is-python3 \
  python3-flask python3-sqlalchemy python3-lxml \
  slimit libsqlite3-dev gdb git firefox xvfb netcat-openbsd \
  libc6-dev-i386

if ! id httpd >/dev/null 2>&1; then
  useradd -m -s /bin/bash httpd
  echo "httpd:6858" | chpasswd
fi

LAB_ROOT="${LAB_ROOT:-/home/httpd.lab}"
ln -sfn "$LAB_ROOT/lab" /home/httpd/lab
cp -f "$LAB_ROOT/libs/libcrypto.so.0.9.8" /usr/lib/ 2>/dev/null || true
cp -f "$LAB_ROOT/libs/libssl.so.0.9.8" /usr/lib/ 2>/dev/null || true
chown -R httpd:httpd /home/httpd
echo "Provision complete. Grade with: sudo sysctl -w kernel.randomize_va_space=0 && sudo -u httpd bash -c 'cd /home/httpd/lab && make check'"
