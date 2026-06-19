#!/bin/bash
# Add lab service UIDs to env/passwd for check-lab2.py / check_lab3.py clean_env().
set -e
cd /home/httpd/lab
MARK="u61018"
for f in env/passwd env/passwd-; do
  grep -q "$MARK" "$f" && continue
  cat >>"$f" <<'EOF'
u61009:x:61009:1000::/:/bin/false
u61010:x:61010:61010::/:/bin/false
u61011:x:61011:1000::/:/bin/false
u61012:x:61012:1000::/:/bin/false
u61013:x:61013:1000::/:/bin/false
u61014:x:61014:1000::/:/bin/false
u61015:x:61015:1000::/:/bin/false
u61016:x:61016:1000::/:/bin/false
u61017:x:61017:1000::/:/bin/false
u61018:x:61018:1000::/:/bin/false
EOF
done
