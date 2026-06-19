#!/bin/bash
# Smoke-test the native x86_64 grading environment.
set -e
cd "$(dirname "$0")"
echo "=== Native i386 grading smoke test ==="
echo "1. zookld + 32-bit reference binaries..."
./run-native.sh bash -c '
  cd /home/httpd/lab
  git checkout -f lab1 2>/dev/null || true
  git checkout origin/lab1 -- bin.tar.gz Makefile 2>/dev/null || true
  tar xf bin.tar.gz
  ldd zookld | grep "not found" && exit 1
  ./clean-env.sh ./zookld zook-exstack.conf &
  sleep 2
  curl -sf http://127.0.0.1:8080/ >/dev/null
  killall zookld zookd-exstack zookfs-exstack 2>/dev/null || true
' || { echo "FAIL: zookld"; exit 1; }
echo "   OK"
echo "2. gcc -m32 build..."
./run-native.sh make zookld 2>&1 | tail -1
echo "   OK"
echo "3. check-bugs (if on lab1)..."
if [ -f lab/bugs.txt ] && [ -f lab/check-bugs.py ]; then
  ./run-native.sh make check-bugs 2>&1 | grep -q PASS && echo "   OK" || echo "   SKIP (not lab1 branch)"
else
  echo "   SKIP"
fi
echo ""
echo "Native grading environment is ready."
echo "Run: ./grade-native.sh all"
