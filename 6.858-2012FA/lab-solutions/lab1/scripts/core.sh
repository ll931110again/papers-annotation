#!/bin/bash
cd /home/httpd/lab
tar xf bin.tar.gz 2>/dev/null
ulimit -c unlimited
echo '/tmp/core.%e.%p' > /proc/sys/kernel/core_pattern 2>/dev/null || true

killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true
./clean-env.sh ./zookld zook-exstack.conf &
sleep 1
python exploit-2a.py localhost 8080
sleep 1
killall zookld zookd-exstack zookfs-exstack 2>/dev/null || true
ls -la /tmp/core* 2>/dev/null || echo "no core"
CORE=$(ls /tmp/core*zookd* 2>/dev/null | head -1)
if [ -n "$CORE" ]; then
  gdb -batch zookd-exstack "$CORE" -ex "info registers eip esp ebp" -ex "x/8wx \$esp"
fi
