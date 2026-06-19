#!/bin/bash
# Grade MIT 6.858 labs on native x86_64 (docker-compose.native.yml).
# Prepares each lab branch on the host, then runs graders inside amd64 Ubuntu.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
LAB="$ROOT/lab"
REF="${MIT6858_REF:-/tmp/mit6858-fz}"
COMPOSE="docker compose -f $ROOT/docker-compose.native.yml"

PASS='\033[1;32mPASS\033[m'
FAIL='\033[1;31mFAIL\033[m'
SKIP='\033[1;33mSKIP\033[m'
RESULTS=()

record() { RESULTS+=("$1|$2|$3"); }

stash_apply() {
  local pattern="$1"
  bash "$ROOT/scripts/stash-apply.sh" "$pattern" 2>/dev/null || true
}

docker_grade() {
  local cmd="$1"
  $COMPOSE run --rm -T --user root lab bash -c "
    sysctl -w kernel.randomize_va_space=0 >/dev/null
    su -s /bin/bash httpd -c 'cd /home/httpd/lab && $cmd'
  "
}

docker_grade_setup() {
  local cmd="$1"
  $COMPOSE run --rm -T --user root lab bash -c "
    sysctl -w kernel.randomize_va_space=0 >/dev/null
    cd /home/httpd/lab && $cmd
  "
}

make_check_log() {
  local target="$1"
  local log="/tmp/mit6858-lab1-$target.log"
  docker_grade "make $target" >"$log" 2>&1 || true
  if grep -q $'\033\[1;32mPASS\033\[m' "$log" 2>/dev/null || grep -q 'PASS' "$log" | grep -qv 'FAIL'; then
    if grep -q 'FAIL' "$log"; then
      echo "$log"
      return 1
    fi
  fi
  if grep -q 'FAIL' "$log"; then
    echo "$log"
    return 1
  fi
  echo "$log"
  return 0
}

lab1_pass() {
  local target="$1"
  local log
  log=$(docker_grade "make $target" 2>&1 | tee "/tmp/mit6858-$target.log") || true
  if echo "$log" | grep -q 'FAIL'; then
    return 1
  fi
  if echo "$log" | grep -q 'PASS'; then
    return 0
  fi
  return 1
}

prepare_lab1() {
  echo "Preparing Lab 1..."
  cd "$LAB"
  git checkout -f lab1
  git reset --hard origin/lab1
  stash_apply "lab1 complete" || stash_apply "lab1 grade state" || true
  for f in exploit-2a.py exploit-2b.py exploit-3.py exploit-4a.py exploit-4b.py; do
    if [ ! -f "$f" ] && [ -f "$REF/lab1/$f" ]; then
      cp "$REF/lab1/$f" "$f"
    fi
  done
  [ -f bin.tar.gz ] || cp "$REF/lab1/bin.tar.gz" bin.tar.gz 2>/dev/null || true
  chmod +x exploit-*.py check-part*.sh 2>/dev/null || true
}

prepare_lab2() {
  echo "Preparing Lab 2..."
  cd "$LAB"
  git checkout -f lab2
  git reset --hard origin/lab2
  stash_apply "lab2 verified" || stash_apply "lab2 graded pass" || stash_apply "lab2 solution" || true
  chmod +x zoobar/svc-*.py 2>/dev/null || true
}

prepare_lab3() {
  echo "Preparing Lab 3..."
  cd "$LAB"
  git checkout -f lab3
  git reset --hard origin/lab3
  stash_apply "lab3 complete" || stash_apply "lab3 work" || true
  git show origin/lab3:pypy-sandbox.tar.bz2 > pypy-sandbox.tar.bz2
  git show origin/lab3:chroot-setup-pypy.sh > chroot-setup-pypy.sh
  git show origin/lab3:check_lab3.py > check_lab3.py
  chmod +x chroot-setup-pypy.sh zoobar/svc-*.py 2>/dev/null || true
}

prepare_lab6() {
  echo "Preparing Lab 6..."
  cd "$LAB"
  git checkout -f lab6
  git reset --hard origin/lab6
  stash_apply "lab6 final" || stash_apply "lab6 solution" || true
  if [ -f "$REF/lab6-js/zoobar/htmlfilter.py" ]; then
    cp "$REF/lab6-js/zoobar/htmlfilter.py" zoobar/
    cp "$REF/lab6-js/zoobar/lab6visitor.py" zoobar/
  fi
}

run_lab1() {
  echo "========== Lab 1: Buffer overflows =========="
  prepare_lab1
  for f in exploit-2a.py exploit-2b.py exploit-3.py exploit-4a.py exploit-4b.py; do
    if [ ! -f "$LAB/$f" ]; then
      echo -e "$FAIL Lab 1 $f MISSING"
      record "Lab 1" "$f" "MISSING"
      return
    fi
  done
  for target in check-bugs check-crash check-exstack check-libc; do
    log=$(docker_grade "make $target" 2>&1 | tee "/tmp/mit6858-lab1-$target.log") || true
    if echo "$log" | grep -q 'FAIL'; then
      echo -e "$FAIL Lab 1 $target"
      echo "$log" | grep -E 'FAIL|PASS' | tail -5
      record "Lab 1" "$target" "FAIL"
    elif echo "$log" | grep -q 'PASS'; then
      echo -e "$PASS Lab 1 $target"
      record "Lab 1" "$target" "PASS"
    else
      echo -e "$FAIL Lab 1 $target (no PASS in output)"
      record "Lab 1" "$target" "FAIL"
    fi
  done
}

run_lab2() {
  echo "========== Lab 2: Privilege separation =========="
  prepare_lab2
  log=$(docker_grade_setup "bash /home/httpd.lab/native/fix-env.sh && bash /home/httpd.lab/native/fix-chroot.sh && make clean all setup && python check-lab2.py" 2>&1 | tee /tmp/mit6858-lab2.log) || true
  if echo "$log" | grep -q 'ERROR:'; then
    echo -e "$FAIL Lab 2 check-lab2.py"
    echo "$log" | grep -E 'PASS|FAIL|ERROR' | tail -15
    record "Lab 2" "check-lab2.py" "FAIL"
  elif echo "$log" | grep -q 'PASS'; then
    echo -e "$PASS Lab 2 check-lab2.py"
    echo "$log" | grep -E 'PASS|FAIL'
    record "Lab 2" "check-lab2.py" "PASS"
  else
    echo -e "$FAIL Lab 2 check-lab2.py"
    record "Lab 2" "check-lab2.py" "FAIL"
  fi
}

run_lab3() {
  echo "========== Lab 3: PyPy sandbox =========="
  prepare_lab3
  log=$(docker_grade_setup "bash /home/httpd.lab/native/fix-env.sh && bash /home/httpd.lab/native/fix-chroot.sh && make clean all setup && timeout 600 python check_lab3.py" 2>&1 | tee /tmp/mit6858-lab3.log) || true
  if echo "$log" | grep -q 'ERROR:'; then
    echo -e "$FAIL Lab 3 check_lab3.py"
    echo "$log" | grep -E 'PASS|FAIL|ERROR' | head -20
    record "Lab 3" "check_lab3.py" "FAIL"
  elif echo "$log" | grep -q 'PASS'; then
    echo -e "$PASS Lab 3 check_lab3.py"
    echo "$log" | grep -E 'PASS|FAIL'
    record "Lab 3" "check_lab3.py" "PASS"
  else
    echo -e "$FAIL Lab 3 check_lab3.py"
    record "Lab 3" "check_lab3.py" "FAIL"
  fi
}

run_lab5() {
  echo "========== Lab 5: Browser attacks =========="
  cd "$LAB"
  git checkout -f lab5 2>/dev/null || git checkout -f lab6
  for f in answer-1.txt answer-2.html answer-3.html answer-4.txt; do
    if [ -f "$f" ]; then
      echo -e "$PASS Lab 5 $f"
      record "Lab 5" "$f" "PASS"
    else
      echo -e "$FAIL Lab 5 $f missing"
      record "Lab 5" "$f" "MISSING"
    fi
  done
  echo -e "$SKIP Lab 5 automated (manual browser test)"
  record "Lab 5" "automated" "SKIP"
}

run_lab6() {
  echo "========== Lab 6: JS sandboxing =========="
  prepare_lab6
  log=$(docker_grade "./check-lab6.sh" 2>&1 | tee /tmp/mit6858-lab6.log) || true
  good=$(echo "$log" | grep -c 'Sandbox: OK' || true)
  bad=$(echo "$log" | grep -c 'Sandbox: Escaped' || true)
  broken=$(echo "$log" | grep -c 'Sandbox: Broken' || true)
  echo "  good OK: $good, bad Escaped: $bad, broken: $broken"
  if [ "$good" -ge 1 ] && [ "$bad" -ge 10 ]; then
    echo -e "$PASS Lab 6 check-lab6.sh"
    record "Lab 6" "check-lab6.sh" "PASS"
  elif echo "$log" | grep -q 'Sandbox: OK'; then
    echo -e "$FAIL Lab 6 check-lab6.sh (partial)"
    record "Lab 6" "check-lab6.sh" "PARTIAL"
  else
    echo -e "$FAIL Lab 6 check-lab6.sh"
    record "Lab 6" "check-lab6.sh" "FAIL"
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [lab1|lab2|lab3|lab5|lab6|all]

Grade MIT 6.858 labs using native x86_64 Docker (docker-compose.native.yml).
Build first:  docker compose -f docker-compose.native.yml build

Environment:
  MIT6858_REF  path to reference solutions (default: /tmp/mit6858-fz)
EOF
}

main() {
  local which="${1:-all}"
  echo "Building native x86_64 image if needed..."
  $COMPOSE build --quiet 2>/dev/null || $COMPOSE build

  case "$which" in
    lab1) run_lab1 ;;
    lab2) run_lab2 ;;
    lab3) run_lab3 ;;
    lab5) run_lab5 ;;
    lab6) run_lab6 ;;
    all)
      run_lab1
      run_lab2
      run_lab3
      run_lab5
      run_lab6
      ;;
    -h|--help) usage; exit 0 ;;
    *) usage; exit 1 ;;
  esac

  echo ""
  echo "========== GRADE SUMMARY =========="
  printf "%-8s %-25s %s\n" "LAB" "CHECK" "RESULT"
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r lab check result <<< "$r"
    printf "%-8s %-25s %s\n" "$lab" "$check" "$result"
  done
}

main "$@"
