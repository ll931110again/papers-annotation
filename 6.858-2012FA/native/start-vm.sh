#!/bin/bash
# Start or create the Lima x86_64 VM for native grading.
set -e
cd "$(dirname "$0")"
NAME=mit6858

if ! command -v limactl >/dev/null; then
  echo "Installing Lima..."
  brew install lima
fi

if limactl list "$NAME" 2>/dev/null | grep -q Running; then
  echo "VM $NAME already running"
elif limactl list "$NAME" 2>/dev/null | grep -q "$NAME"; then
  limactl start "$NAME"
else
  limactl start --name="$NAME" lima.yaml
fi

echo ""
echo "VM ready. Next steps:"
echo "  limactl shell $NAME -- sudo bash /home/httpd.lab/native/provision.sh"
echo "  ./grade-native.sh all    # or grade inside VM:"
echo "  limactl shell $NAME -- sudo sysctl -w kernel.randomize_va_space=0"
echo "  limactl shell $NAME -- sudo -u httpd bash -c 'cd /home/httpd/lab && make check-exstack'"
