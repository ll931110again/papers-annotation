#!/bin/bash
cd /home/httpd/lab
tar xf bin.tar.gz 2>/dev/null
./check-part2.sh zook-exstack.conf ./exploit-2a.py
./check-part2.sh zook-exstack.conf ./exploit-2b.py
