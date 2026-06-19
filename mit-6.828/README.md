# MIT 6.828 (Fall 2012) — Operating System Engineering

Self-study track for [MIT 6.828 Fall 2012](https://pdos.csail.mit.edu/6.828/2012/overview.html): study xv6, then build **JOS** (Josh's Operating System) across six labs.

## Course structure

| Phase | Topic | Materials |
|-------|-------|-----------|
| Lectures 1–12 | xv6 internals | [xv6 book](https://pdos.csail.mit.edu/6.828/2012/xv6.html) |
| Lectures 13+ | Research topics + JOS extensions | Papers on course site |
| Labs 1–5 | Individual JOS milestones | `lab/` directory |
| Lab 6 | Network driver + lwIP stack | `lab/` directory |

### JOS lab milestones

1. **Booting** — PC bootstrap, printf, stack backtrace
2. **Memory management** — physical pages, page tables, kernel address space
3. **User environments** — processes, system calls, exception handling
4. **Preemptive multitasking** — timer interrupts, round-robin scheduling
5. **File system & spawn** — IDE driver, FS server, `spawn`, shell
6. **Network driver** — E1000, lwIP, HTTP server

## Setup (macOS)

```bash
brew install i686-elf-gcc i686-elf-binutils qemu
```

`lab/conf/env.mk` is configured for the Homebrew toolchain. Two flags are required on modern compilers:

- `-std=gnu99` — JOS predates C23
- `-fno-pic` — prevents GOT/PLT sections that cause triple-fault boot loops

### STABS debug symbols

Lab 1 exercise 12+ needs STABS (`-gstabs`), which modern macOS GCC no longer emits. Build the kernel in Linux Docker, then run QEMU on the host:

```bash
make -f Makefile.docker grade-lab1   # build in Docker + grade on host
```

Or build only:

```bash
make -f Makefile.docker build-linux
make qemu-nox                        # in lab/, after restoring conf/env.mk
```

## Working on labs

```bash
cd lab
git checkout -b labN origin/labN   # after completing lab N-1
make                              # build kernel image
make qemu-nox                     # run in QEMU (Ctrl-a x to exit)
make grade                        # official autograder (needs Python 2 + Linux)
```

For macOS grading without Python 2:

```bash
python3 ../scripts/grade_lab1.py --no-build   # after build-linux
```

## Progress

- [x] Lab 1 — Booting (printf `%o`, backtrace, `debuginfo_eip`) — **50/50**
- [x] Lab 2 — Memory management (pmap, page tables, kernel VM)
- [x] Lab 3 — User environments (processes, syscalls, exceptions)
- [x] Lab 4 — Preemptive multitasking (timer, scheduling, IPC)
- [x] Lab 5 — File system & spawn (IDE, FS server, `spawn`, shell)
- [x] Lab 6 — Network driver (E1000, lwIP, echo server, HTTP) — **105/105**

## Grading on macOS

Build once in Docker, then grade on the host (native QEMU):

```bash
make -f Makefile.docker build-linux

python3 scripts/grade_lab1.py --no-build
python3 scripts/grade_lab.py 2 --no-build
python3 scripts/grade_lab.py 3 --no-build   # expects user/hello as init
python3 scripts/grade_lab.py 4 --no-build   # expects user/primes as init
python3 scripts/grade_lab.py 5 --no-build   # smoke test (icode boot)
python3 scripts/grade_lab5.py               # full lab5 suite (rebuilds per test)
python3 scripts/grade_lab6.py               # lab6 network suite (rebuilds per test)
make -f Makefile.docker grade-lab5            # build + smoke grade
```

Lab 3–4 default kernels embed `user/icode` on the lab5 branch. Rebuild with
`-DTEST=user_hello` or `-DTEST=user_primes` in Docker for those smoke tests, or
use `grade_lab5.py` which handles test-specific builds automatically.

The official `grade-labN` scripts invoke `make` and require Linux + Python 2.

## Lab 1 changes

- `lib/printfmt.c` — octal (`%o`) formatting
- `kern/monitor.c` — `mon_backtrace()` + `backtrace` monitor command
- `kern/kdebug.c` — `stab_binsearch()` for line numbers (`N_SLINE`)

## References

- [Course home](https://pdos.csail.mit.edu/6.828/2012/)
- [Lab 1](https://pdos.csail.mit.edu/6.828/2012/labs/lab1/)
- [Tools](https://pdos.csail.mit.edu/6.828/2012/tools.html)
- JOS source: `git clone https://pdos.csail.mit.edu/6.828/2012/jos.git`
