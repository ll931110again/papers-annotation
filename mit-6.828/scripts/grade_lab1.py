#!/usr/bin/env python3
"""Run lab1 grade checks on the host (no Python 2 / GDB stub required)."""

import os
import re
import subprocess
import sys
import time
import select

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = os.path.join(ROOT, "lab")
os.chdir(LAB)

BACKTRACE_RE = re.compile(
    r"^ *ebp +f01[0-9a-z]{5} +eip +f0100[0-9a-z]{3} +args +([0-9a-z]+)",
    re.MULTILINE,
)


def qemu_env():
    env = os.environ.copy()
    for candidate in (
        "/opt/homebrew/bin/qemu-system-i386",
        "/usr/local/bin/qemu-system-i386",
        "qemu-system-i386",
    ):
        if candidate == "qemu-system-i386" or os.path.isfile(candidate):
            env["QEMU"] = candidate
            break
    return env


def gdb_port():
    uid = os.getuid()
    return uid % 5000 + 25000


def run_qemu(timeout=30):
    env = qemu_env()
    qemu = env["QEMU"]
    port = gdb_port()
    cmd = [
        qemu, "-nographic",
        "-drive", "file=obj/kern/kernel.img,format=raw,if=ide",
        "-serial", "mon:stdio",
        "-gdb", f"tcp::{port}",
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
    )
    output = b""
    start = time.time()
    fd = proc.stdout.fileno()
    while time.time() - start < timeout:
        ready, _, _ = select.select([fd], [], [], 0.2)
        if ready:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            output += chunk
            if b"Physical memory:" in output:
                break
            if b"K>" in output:
                break
        elif proc.poll() is not None:
            break
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    return output.decode("utf-8", errors="replace")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-build", action="store_true",
                        help="use existing obj/kern/kernel.img")
    args = parser.parse_args()

    if not args.no_build:
        print("building (use 'make -f ../Makefile.docker build-linux' for STABS)...")
        subprocess.run(["make", "-s"], check=True)
    elif not os.path.exists("obj/kern/kernel.img"):
        sys.exit("obj/kern/kernel.img missing; run build-linux first")
    print("running QEMU...")
    out = run_qemu()
    open("jos.out", "w").write(out)

    score = 0
    total = 50

    def check(name, points, ok, detail=""):
        nonlocal score
        print(f"{name}: {'OK' if ok else 'FAIL'}")
        if detail and not ok:
            print(f"    {detail}")
        if ok:
            score += points

    check("printf", 20, "6828 decimal is 15254 octal!" in out)
    matches = BACKTRACE_RE.findall(out)
    check("backtrace count", 10, len(matches) == 8, f"got {len(matches)} frames")
    expected_args = "\n".join("%08x" % n for n in [0, 0, 1, 2, 3, 4, 5])
    got_args = "\n".join(matches[:7])
    check("backtrace arguments", 10, got_args == expected_args,
          f"got:\n  {got_args}\nexpected:\n  {expected_args}")
    sym_matches = re.findall(r"kern/init.c:[0-9]+: +([^+]*)\+", out)
    expected_syms = "\n".join(["test_backtrace"] * 6 + ["i386_init"])
    check("backtrace symbols", 5,
          "\n".join(sym_matches[:7]) == expected_syms,
          f"got {sym_matches[:7]}")
    line_matches = re.findall(r"([^ ]*init.c:([0-9]+):) +test_backtrace\+", out)
    line_ok = bool(line_matches) and all(5 <= int(m[1]) <= 50 for m in line_matches)
    check("backtrace lines", 5, line_ok, f"matches={line_matches}")

    print(f"Score: {score}/{total}")
    sys.exit(0 if score == total else 1)


if __name__ == "__main__":
    main()
