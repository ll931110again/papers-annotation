#!/bin/bash
# Run a command in the native x86_64 grading container (ASLR off, as httpd).
set -e
cd "$(dirname "$0")"
args=$(printf '%q ' "$@")
docker compose -f docker-compose.native.yml run --rm -T --user root lab bash -c "
  sysctl -w kernel.randomize_va_space=0 >/dev/null
  exec su -s /bin/bash httpd -c 'cd /home/httpd/lab && $args'
"
