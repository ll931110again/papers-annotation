# MIT 6.858 (Fall 2012) Labs

Dockerized environment for the [MIT 6.858](https://css.csail.mit.edu/6.858/2012/) security labs.

## Quick start (native x86 grading — recommended)

Uses **x86_64 Ubuntu** (`linux/amd64`) to run 32-bit (`-m32`) lab binaries with correct stack layout. Much more reliable than `linux/386` QEMU on Apple Silicon.

```bash
docker compose -f docker-compose.native.yml build
./grade-native.sh all          # grade every lab
./grade-native.sh lab1         # single lab
./run-native.sh make check-exstack
```

## QEMU fallback (Apple Silicon, slower)

```bash
docker compose build
docker compose run --rm --user root lab bash -c \
  'cd /home/httpd/lab && make setup && python check-lab2.py'
```

## Full VM (Firefox + PyPy sandbox)

For Lab 3 PyPy and Lab 6 Firefox grading without Docker limits:

```bash
brew install lima
cd native && ./start-vm.sh
limactl shell mit6858 -- sudo bash /home/httpd.lab/native/provision.sh
limactl shell mit6858 -- sudo sysctl -w kernel.randomize_va_space=0
limactl shell mit6858 -- sudo -u httpd bash -c 'cd /home/httpd/lab && ./check-lab6.sh'
```

## Lab status

| Lab | Branch | Status |
|-----|--------|--------|
| **Lab 1** — Buffer overflows | `lab1` | `check-bugs`, `check-crash` pass. Exercises 3–4 exploits use header-overflow + ret2libc (libc unlink `0x40a563b0`); **stack ebp must be tuned on native i386** — QEMU user emulation uses different stack layout. |
| **Lab 2** — Privilege separation | `lab2` | **All checks pass** (`check-lab2.py`) |
| **Lab 3** — PyPy sandbox | `lab3` | Full solution in stash `lab3 complete`: per-user `/tmp`, RPC proflib, lab2 services merged. PyPy sandbox SIGIOT under QEMU. |
| **Lab 4** — Attacking server isolation | `lab4/` | Review files `lab4-code0.txt`, `lab4-code1.txt` (no peer tarball in repo; reviews based on our Lab 2 + reference) |
| **Lab 5** — Browser attacks | `lab5` | `answer-1.txt` … `answer-4.txt` (also on `lab6` branch) |
| **Lab 6** — JS sandboxing | `lab6` | `htmlfilter.py` + `lab6visitor.py` — filter rewriter runs; browser grading needs Firefox |
| **Lab 7** — Final project | — | Skipped (open-ended) |

## Git stashes (solutions)

```bash
git stash list
# lab1 complete  — bugs, exploits, http.c fixes
# lab2 verified  — full privilege separation
# lab3 complete  — lab2 + pypysandbox + RPC profiles
# lab6 solution  — htmlfilter + lab6visitor
```

## Lab 2 solution highlights

- Split services: `auth_svc`, `log_svc`, `xfer_svc` via `zooksvc` + RPC
- Databases: `auth.db`, `transfer.db`, `zoobars.db`, `person.db`
- Static/dynamic `zookfs` UIDs, CGI uid pinning, `password.cgi` / `db` blocking

## Lab 5 answers

- `answer-1.txt` — XSS cookie theft URL
- `answer-2.html` — CSRF (10 zoobars → attacker)
- `answer-3.html` — Phishing / side-channel
- `answer-4.txt` — Profile worm

## Notes

- **Grading:** prefer `./grade-native.sh` (`docker-compose.native.yml`, `linux/amd64`) over `docker compose` (`linux/386`)
- ASLR must be off for Lab 1 exploits: `sysctl -w kernel.randomize_va_space=0`
- Lab 1 exploits 3–4: tune `STACK_SAVED_EBP` with `./run-native.sh python scripts/brute_header.py` if checks fail
- Lab 3 requires `pypy-sandbox.tar.bz2` (from `git show origin/lab3:pypy-sandbox.tar.bz2`)
- Lab 6 browser tests: `./run-native.sh ./check-lab6.sh` (needs Firefox + Xvfb in native image)
- Reference solutions path: `MIT6858_REF=/tmp/mit6858-fz` (used by `grade-native.sh`)
