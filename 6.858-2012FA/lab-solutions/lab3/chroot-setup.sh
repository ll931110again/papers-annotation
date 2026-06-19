#!/bin/sh -x
if id | grep -qv uid=0; then
    echo "Must run setup as root"
    exit 1
fi

create_socket_dir() {
    local dirname="$1"
    local ownergroup="$2"
    local perms="$3"

    mkdir -p $dirname
    chown $ownergroup $dirname
    chmod $perms $dirname
}

set_perms() {
    local ownergroup="$1"
    local perms="$2"
    local pn="$3"

    chown $ownergroup $pn
    chmod $perms $pn
}

rm -rf /jail
mkdir -p /jail
cp -p index.html /jail
cp -p password.cgi /jail

./chroot-copy.sh zookd /jail
./chroot-copy.sh zookfs /jail
./chroot-copy.sh zooksvc /jail

./chroot-copy.sh /usr/bin/env /jail
./chroot-copy.sh /usr/bin/python /jail

mkdir -p /jail/usr/lib /jail/usr/lib/i386-linux-gnu
cp -r /usr/lib/python2.7 /jail/usr/lib
cp /usr/lib/i386-linux-gnu/libsqlite3.so.0 /jail/usr/lib/i386-linux-gnu 2>/dev/null || \
    cp /usr/lib/libsqlite3.so.0 /jail/usr/lib

mkdir -p /jail/usr/local/lib
cp -r /usr/local/lib/python2.7 /jail/usr/local/lib 2>/dev/null || true

mkdir -p /jail/etc
cp /etc/localtime /jail/etc/
cp /etc/timezone /jail/etc/ 2>/dev/null || true

mkdir -p /jail/usr/share/zoneinfo
cp -r /usr/share/zoneinfo/America /jail/usr/share/zoneinfo/ 2>/dev/null || true

create_socket_dir /jail/echosvc 61010:61010 755
create_socket_dir /jail/authsvc 61016:61016 711
create_socket_dir /jail/logsvc 61017:61018 770
create_socket_dir /jail/xfersvc 61018:61018 711

mkdir -p /jail/tmp/sandbox-root
chmod a+rwxt /jail/tmp

mkdir -p /jail/dev
mknod /jail/dev/urandom c 1 9 2>/dev/null || true

cp -r zoobar /jail/
rm -rf /jail/zoobar/db

python /jail/zoobar/zoodb.py init-person
python /jail/zoobar/zoodb.py init-transfer
python /jail/zoobar/zoodb.py init-auth
python /jail/zoobar/zoodb.py init-zoobars

set_perms 61012:1000 775 /jail/zoobar
set_perms 61012:1000 775 /jail/zoobar/db
set_perms 61012:1000 775 /jail/zoobar/db/person
set_perms 61012:1000 775 /jail/zoobar/db/person/person.db

set_perms 61015:1000 775 /jail/zoobar/index.cgi

set_perms 61016:1000 700 /jail/zoobar/db/auth
set_perms 61016:1000 700 /jail/zoobar/db/auth/auth.db

set_perms 61017:1000 700 /jail/zoobar/db/transfer
set_perms 61017:1000 700 /jail/zoobar/db/transfer/transfer.db

set_perms 61018:1000 700 /jail/zoobar/db/zoobars
set_perms 61018:1000 700 /jail/zoobar/db/zoobars/zoobars.db

chmod +x /jail/zoobar/svc-*.py
