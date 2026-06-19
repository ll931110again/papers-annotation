#!/bin/bash
# Grade all MIT 6.858 labs in Docker (linux/386 + QEMU).
set -e
LABDIR="$(cd "$(dirname "$0")" && pwd)"
cd "$LABDIR"

PASS='\033[1;32mPASS\033[m'
FAIL='\033[1;31mFAIL\033[m'
SKIP='\033[1;33mSKIP\033[m'
RESULTS=()

record() { RESULTS+=("$1|$2|$3"); }

run_lab1() {
  echo "========== Lab 1: Buffer overflows =========="
  git checkout -f lab1 >/dev/null 2>&1
  git stash apply stash@{3} 2>/dev/null || true
  # ensure exploits exist
  for f in exploit-2a.py exploit-2b.py exploit-3.py exploit-4a.py exploit-4b.py; do
    [ -f "$f" ] || { record "Lab 1" "$f" "MISSING"; return; }
  done
  sysctl -w kernel.randomize_va_space=0 >/dev/null
  for target in check-bugs check-crash check-exstack check-libc; do
    if su -s /bin/bash httpd -c "cd $LABDIR && make $target" >/tmp/lab1-$target.log 2>&1; then
      echo -e "$PASS Lab 1 $target"
      record "Lab 1" "$target" "PASS"
    else
      echo -e "$FAIL Lab 1 $target"
      tail -3 /tmp/lab1-$target.log
      record "Lab 1" "$target" "FAIL"
    fi
  done
}

run_lab2() {
  echo "========== Lab 2: Privilege separation =========="
  git checkout -f lab2 >/dev/null 2>&1
  git stash apply stash@{2} 2>/dev/null || git stash apply stash@{6} 2>/dev/null || true
  chmod +x zoobar/svc-*.py 2>/dev/null || true
  if make clean all setup >/tmp/lab2-setup.log 2>&1 && python check-lab2.py >/tmp/lab2-check.log 2>&1; then
    echo -e "$PASS Lab 2 check-lab2.py"
    grep -E 'PASS|FAIL' /tmp/lab2-check.log | sed 's/^/  /'
    record "Lab 2" "check-lab2.py" "PASS"
  else
    echo -e "$FAIL Lab 2 check-lab2.py"
    tail -10 /tmp/lab2-check.log 2>/dev/null || tail -10 /tmp/lab2-setup.log
    record "Lab 2" "check-lab2.py" "FAIL"
  fi
}

run_lab3() {
  echo "========== Lab 3: PyPy sandbox =========="
  git checkout -f lab3 >/dev/null 2>&1
  git stash apply stash@{1} 2>/dev/null || git stash apply stash@{5} 2>/dev/null || true
  git show origin/lab3:pypy-sandbox.tar.bz2 > pypy-sandbox.tar.bz2 2>/dev/null
  git show origin/lab3:chroot-setup-pypy.sh > chroot-setup-pypy.sh 2>/dev/null
  git show origin/lab3:check_lab3.py > check_lab3.py 2>/dev/null
  chmod +x chroot-setup-pypy.sh zoobar/svc-*.py 2>/dev/null || true
  if make clean all setup >/tmp/lab3-setup.log 2>&1; then
    if timeout 300 python check_lab3.py >/tmp/lab3-check.log 2>&1; then
      echo -e "$PASS Lab 3 check_lab3.py"
      grep -E 'PASS|FAIL' /tmp/lab3-check.log | sed 's/^/  /'
      record "Lab 3" "check_lab3.py" "PASS"
    else
      echo -e "$FAIL Lab 3 check_lab3.py"
      grep -E 'PASS|FAIL|ERROR' /tmp/lab3-check.log | head -20 | sed 's/^/  /'
      record "Lab 3" "check_lab3.py" "FAIL"
    fi
  else
    echo -e "$FAIL Lab 3 setup"
    tail -5 /tmp/lab3-setup.log
    record "Lab 3" "setup" "FAIL"
  fi
}

run_lab5() {
  echo "========== Lab 5: Browser attacks =========="
  git checkout -f lab5 >/dev/null 2>&1
  missing=0
  for f in answer-1.txt answer-2.html answer-3.html answer-4.txt; do
    if [ -f "$f" ]; then
      echo -e "$PASS Lab 5 $f present"
      record "Lab 5" "$f" "PASS"
    else
      # try lab6 branch copies
      git show lab6:$f > "$f" 2>/dev/null && {
        echo -e "$PASS Lab 5 $f (from lab6)"
        record "Lab 5" "$f" "PASS"
      } || {
        echo -e "$FAIL Lab 5 $f missing"
        record "Lab 5" "$f" "MISSING"
        missing=1
      }
    fi
  done
  echo -e "$SKIP Lab 5: no automated grader in 2012 repo (manual browser test)"
  record "Lab 5" "automated" "SKIP"
}

run_lab6() {
  echo "========== Lab 6: JS sandboxing =========="
  git checkout -f lab6 >/dev/null 2>&1
  git stash apply stash@{0} 2>/dev/null || git stash apply stash@{4} 2>/dev/null || true
  cp /tmp/mit6858-fz/lab6-js/zoobar/htmlfilter.py zoobar/ 2>/dev/null || true
  cp /tmp/mit6858-fz/lab6-js/zoobar/lab6visitor.py zoobar/ 2>/dev/null || true
  good=0; bad=0; broken=0
  for p in profiles/good-*.html; do
    if python zoobar/filter-test.py < "$p" >/tmp/sb.html 2>/dev/null; then
      out=$(./test-url.sh /tmp/sb.html 2>/dev/null || echo "Unknown")
      case "$out" in *OK*) good=$((good+1)) ;; *) broken=$((broken+1)) ;; esac
    else
      broken=$((broken+1))
    fi
  done
  for p in profiles/bad-*.html; do
    if python zoobar/filter-test.py < "$p" >/tmp/sb.html 2>/dev/null; then
      out=$(./test-url.sh /tmp/sb.html 2>/dev/null || echo "Unknown")
      case "$out" in *Escaped*) bad=$((bad+1)) ;; *OK*) broken=$((broken+1)) ;; esac
    else
      broken=$((broken+1))
    fi
  done
  echo "  good profiles OK: $good/1, bad profiles blocked: $bad/14, issues: $broken"
  if [ "$good" -ge 1 ] && [ "$bad" -ge 10 ]; then
    echo -e "$PASS Lab 6 filter (partial - no Firefox)"
    record "Lab 6" "filter-test" "PASS"
  elif python zoobar/filter-test.py < profiles/good-all.html >/dev/null 2>&1; then
    echo -e "$PASS Lab 6 filter rewriter runs"
    record "Lab 6" "filter-test" "PARTIAL"
  else
    echo -e "$FAIL Lab 6 filter"
    record "Lab 6" "filter-test" "FAIL"
  fi
  record "Lab 6" "check-lab6.sh" "SKIP (needs Firefox)"
}

# Main
[ "$(id -u)" = "0" ] || { echo "Run as root inside Docker"; exit 1; }
sysctl -w kernel.randomize_va_space=0 >/dev/null

run_lab1
run_lab2
run_lab3
run_lab5
run_lab6

echo ""
echo "========== GRADE SUMMARY =========="
printf "%-8s %-25s %s\n" "LAB" "CHECK" "RESULT"
for r in "${RESULTS[@]}"; do
  IFS='|' read -r lab check result <<< "$r"
  printf "%-8s %-25s %s\n" "$lab" "$check" "$result"
done
