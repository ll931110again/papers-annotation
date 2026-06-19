#!/bin/bash
# Patch chroot-setup.sh for native x86_64 grading (mixed 32-bit zookfs + 64-bit python).
set -e
cd /home/httpd/lab
MARK="# native-x86-grading"
grep -q "$MARK" chroot-setup.sh && exit 0

cat >>chroot-setup.sh <<'PATCH'

# native-x86-grading: passwd/NSS for CGI python (64-bit) inside jail
mkdir -p /jail/lib/i386-linux-gnu /jail/lib/x86_64-linux-gnu
cp /lib/i386-linux-gnu/libnss_files.so.2 /jail/lib/i386-linux-gnu/ 2>/dev/null || true
cp /lib/x86_64-linux-gnu/libnss_files.so.2 /jail/lib/x86_64-linux-gnu/ 2>/dev/null || true
cp /lib/x86_64-linux-gnu/libnss_dns.so.2 /jail/lib/x86_64-linux-gnu/ 2>/dev/null || true
cp /lib/x86_64-linux-gnu/libresolv.so.2 /jail/lib/x86_64-linux-gnu/ 2>/dev/null || true
cp /etc/passwd /jail/etc/passwd 2>/dev/null || true
cp /etc/group /jail/etc/group 2>/dev/null || true
cp /etc/nsswitch.conf /jail/etc/nsswitch.conf 2>/dev/null || true
sed -i 's/^passwd:.*/passwd:         files/' /jail/etc/nsswitch.conf 2>/dev/null || true
sed -i 's/^group:.*/group:          files/' /jail/etc/nsswitch.conf 2>/dev/null || true
PATCH
