#!/bin/bash
cd /home/httpd/lab
tar xf bin.tar.gz 2>/dev/null
./clean-env.sh ./zookld zook-exstack.conf &
sleep 1
ZPID=$(pgrep zookd-exstack | head -1)
FPID=$(pgrep zookfs-exstack | head -1)
echo "zookd=$ZPID zookfs=$FPID"
[ -n "$ZPID" ] && cat /proc/$ZPID/maps | grep stack
[ -n "$FPID" ] && cat /proc/$FPID/maps | grep -E "stack|libc-2"
killall zookld zookd-exstack zookfs-exstack 2>/dev/null
