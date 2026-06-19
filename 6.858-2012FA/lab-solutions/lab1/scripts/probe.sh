#!/bin/bash
set +e
cd /home/httpd/lab
tar xf bin.tar.gz 2>/dev/null
python scripts/probe.py
UNLINK_OFF=$(nm -D /lib/i386-linux-gnu/libc.so.6 | awk '/unlink$/ {print $1}')
echo "unlink@libc = $(python -c "print hex(0x40977000 + 0x$UNLINK_OFF)")"
