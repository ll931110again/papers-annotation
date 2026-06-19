#!/usr/bin/env python3
"""Run lab5 grade checks on the host (build test kernels in Docker, QEMU on macOS)."""

import argparse
import os
import re
import select
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = os.path.join(ROOT, "lab")
DOCKER = os.path.join(ROOT, "Makefile.docker")

DOCKER_SETUP = (
    "apt-get update -qq && "
    "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gcc-multilib make binutils >/dev/null && "
    'printf "GCCPREFIX=\\nQEMU=qemu-system-i386\\nCFLAGS += -std=gnu99 -fno-pic -no-pie\\n" > conf/env.mk'
)


def qemu_path():
    for candidate in (
        "/opt/homebrew/bin/qemu-system-i386",
        "/usr/local/bin/qemu-system-i386",
        "qemu-system-i386",
    ):
        if candidate == "qemu-system-i386" or os.path.isfile(candidate):
            return candidate
    return "qemu-system-i386"


def docker_build(test=None):
    test_flag = ""
    if test:
        test_flag = f'make "INIT_CFLAGS=-DTEST=user_{test}" obj/kern/kernel.img obj/fs/fs.img'
    else:
        test_flag = "make obj/kern/kernel.img obj/fs/fs.img"
    cmd = [
        "docker", "run", "--platform", "linux/amd64", "--rm",
        "-v", f"{LAB}:/lab", "-w", "/lab", "ubuntu:18.04",
        "bash", "-c", f"{DOCKER_SETUP} && {test_flag}",
    ]
    print(f"  building kernel for {test or 'default'}...")
    subprocess.run(cmd, check=True)


def run_qemu(timeout=60, stop_on=None):
    qemu = qemu_path()
    cmd = [
        qemu, "-nographic",
        "-drive", "file=obj/kern/kernel.img,format=raw,if=ide",
        "-drive", "file=obj/fs/fs.img,format=raw,if=ide",
        "-serial", "mon:stdio",
    ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, cwd=LAB)
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
            if stop_on and re.search(stop_on, text, re.MULTILINE):
                break
            if "No runnable environments" in text:
                break
        elif proc.poll() is not None:
            break
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    return output.decode("utf-8", errors="replace")


def match_all(out, *patterns):
    missing = [p for p in patterns if not re.search(p, out)]
    return missing


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-build", action="store_true",
                        help="skip Docker rebuild (only run icode test)")
    args = parser.parse_args()
    os.chdir(LAB)

    score = 0
    total = 75

    def check(name, points, ok, detail=""):
        nonlocal score
        print(f"{name}: {'OK' if ok else 'FAIL'}")
        if detail and not ok:
            print(f"    {detail}")
        if ok:
            score += points

    # hello (FS internal smoke test)
    if not args.no_build:
        docker_build("hello")
    out = run_qemu(timeout=30)
    check("FS smoke (hello)", 5,
          "FS can do I/O" in out and "superblock is good" in out)

    # spawnhello
    if not args.no_build:
        docker_build("spawnhello")
    out = run_qemu(timeout=45)
    check("spawnhello", 10, not match_all(
        out,
        r"i am parent environment 00001001",
        r"hello, world",
        r"i am environment 00001002",
    ))

    # testpteshare
    if not args.no_build:
        docker_build("testpteshare")
    out = run_qemu(timeout=45)
    check("PTE_SHARE (testpteshare)", 10, not match_all(
        out,
        r"fork handles PTE_SHARE right",
        r"spawn handles PTE_SHARE right",
    ))

    # testfdsharing
    if not args.no_build:
        docker_build("testfdsharing")
    out = run_qemu(timeout=45)
    check("PTE_SHARE (testfdsharing)", 5, not match_all(
        out,
        r"read in child succeeded",
        r"read in parent succeeded",
    ))

    # icode (default init)
    if not args.no_build:
        docker_build("icode")
    out = run_qemu(timeout=60)
    check("icode + init + sh", 15, not match_all(
        out,
        r"icode: read /motd",
        r"This is /motd, the message of the day\.",
        r"icode: spawn /init",
        r"init: running",
        r"init: data seems okay",
        r"icode: exiting",
        r"init: bss seems okay",
        r"init: args: 'init' 'initarg1' 'initarg2'",
        r"init: running sh",
    ))

    # testshell (longer timeout)
    if not args.no_build:
        docker_build("testshell")
    out = run_qemu(timeout=90)
    check("testshell", 15, "shell ran correctly" in out)

    # primespipe
    if not args.no_build:
        docker_build("primespipe")
    out = run_qemu(timeout=120, stop_on=r"^1009$")
    primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47}
    prime_ok = all(re.search(rf"^{p}$", out, re.MULTILINE) for p in primes)
    check("primespipe", 15, prime_ok and "997" in out)

    print(f"Score: {score}/{total}")
    sys.exit(0 if score == total else 1)


if __name__ == "__main__":
    main()
