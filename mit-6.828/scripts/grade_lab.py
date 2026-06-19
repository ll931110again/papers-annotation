#!/usr/bin/env python3
"""Generic JOS lab grader: build in Docker, run QEMU on host, match patterns."""

import argparse
import os
import re
import select
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = os.path.join(ROOT, "lab")


def qemu_path():
    for candidate in (
        "/opt/homebrew/bin/qemu-system-i386",
        "/usr/local/bin/qemu-system-i386",
        "qemu-system-i386",
    ):
        if candidate == "qemu-system-i386" or os.path.isfile(candidate):
            return candidate
    return "qemu-system-i386"


def run_qemu(timeout=45, fs=False, lab=0):
    qemu = qemu_path()
    kernel = os.path.join(LAB, "obj/kern/kernel.img")
    cmd = [
        qemu, "-nographic",
        "-drive", f"file={kernel},format=raw,if=ide",
    ]
    if fs:
        fsimg = os.path.join(LAB, "obj/fs/fs.img")
        cmd += ["-drive", f"file={fsimg},format=raw,if=ide"]
    cmd += ["-serial", "mon:stdio"]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL)
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
            text = output.decode("utf-8", errors="replace")
            if lab == 3 and "hello, world" in text:
                break
            if lab == 4 and "CPU 0: 12" in text:
                break
            if lab == 2 and "check_page_installed_pgdir() succeeded!" in text:
                break
            if lab == 5 and "init: running sh" in text:
                break
            if lab == 5 and "No runnable environments" in text:
                break
            if fs and "init: running sh" in text:
                break
            if fs and "No runnable environments" in text:
                break
            if not fs and lab not in (2, 3, 4, 5) and "K>" in text:
                break
            if not fs and lab not in (2, 3, 4, 5) and "No runnable environments" in text:
                break
        elif proc.poll() is not None:
            break
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    return output.decode("utf-8", errors="replace")


def grade_lab2(out):
    tests = [
        ("Physical page allocator", 20, r"check_page_alloc\(\) succeeded!"),
        ("Page management", 20, r"check_page\(\) succeeded!"),
        ("Kernel page directory", 20, r"check_kern_pgdir\(\) succeeded!"),
        ("Page management 2", 10, r"check_page_installed_pgdir\(\) succeeded!"),
    ]
    score = 0
    total = sum(t[1] for t in tests)
    for name, pts, pat in tests:
        ok = re.search(pat, out) is not None
        print(f"{name}: {'OK' if ok else 'FAIL'}")
        if ok:
            score += pts
    print(f"Score: {score}/{total}")
    return score == total


def grade_lab3(out):
    tests = [
        ("User hello", 50, r"hello, world"),
    ]
    score = 0
    total = sum(t[1] for t in tests)
    for name, pts, pat in tests:
        ok = re.search(pat, out) is not None
        print(f"{name}: {'OK' if ok else 'FAIL'}")
        if ok:
            score += pts
    print(f"Score: {score}/{total}")
    return score == total


def grade_lab4(out):
    tests = [
        ("User primes (multiprocess)", 40, r"CPU 0: 12"),
    ]
    score = 0
    total = sum(t[1] for t in tests)
    for name, pts, pat in tests:
        ok = re.search(pat, out) is not None
        print(f"{name}: {'OK' if ok else 'FAIL'}")
        if ok:
            score += pts
    print(f"Score: {score}/{total}")
    return score == total


def grade_lab5(out):
    tests = [
        ("FS boot", 10, r"superblock is good"),
        ("motd", 15, r"This is /motd, the message of the day\."),
        ("init + shell", 25, r"init: running sh"),
    ]
    score = 0
    total = sum(t[1] for t in tests)
    for name, pts, pat in tests:
        ok = re.search(pat, out) is not None
        print(f"{name}: {'OK' if ok else 'FAIL'}")
        if ok:
            score += pts
    print(f"Score: {score}/{total}")
    return score == total


GRADERS = {2: grade_lab2, 3: grade_lab3, 4: grade_lab4, 5: grade_lab5}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("lab", type=int, choices=[2, 3, 4, 5])
    parser.add_argument("--no-build", action="store_true",
                        help="use existing obj/kern/kernel.img")
    args = parser.parse_args()
    os.chdir(LAB)
    if not args.no_build:
        print("building via Docker...")
        subprocess.run(
            ["make", "-f", os.path.join(ROOT, "Makefile.docker"), "build-linux"],
            check=True, cwd=ROOT)
    elif not os.path.exists("obj/kern/kernel.img"):
        print("obj/kern/kernel.img missing; run make -f ../Makefile.docker build-linux")
        sys.exit(1)
    if args.lab == 5 and not os.path.exists("obj/fs/fs.img"):
        print("obj/fs/fs.img missing; run make -f ../Makefile.docker build-linux")
        sys.exit(1)
    print("running QEMU...")
    timeout = 60 if args.lab >= 4 else (45 if args.lab == 3 else 30)
    out = run_qemu(timeout=timeout, fs=(args.lab == 5), lab=args.lab)
    open("jos.out", "w").write(out)
    ok = GRADERS[args.lab](out)
    if args.lab == 5 and ok:
        print("(For full lab5 score use: python3 ../scripts/grade_lab5.py)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
