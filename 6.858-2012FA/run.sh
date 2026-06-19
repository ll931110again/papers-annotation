#!/bin/bash
set +e
cd "$(dirname "$0")"
args=$(printf '%q ' "$@")
docker compose run --rm --user root lab bash -c "
  sysctl -w kernel.randomize_va_space=0 >/dev/null
  exec su -s /bin/bash httpd -c 'cd /home/httpd/lab && $args'
"
