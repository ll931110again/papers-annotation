#!/usr/bin/env python3
"""Grade optional/challenge exercises (sfork, Unix exec)."""

import argparse
import os
import re
import select
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = os.path.join(ROOT, "lab")

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


def docker_build(test, extra_make=""):
    make_flags = (
        f'make {extra_make} CHALLENGE_BINS=1 '
        f'"INIT_CFLAGS=-DTEST_NO_NS -DTEST={test}" '
        f'obj/kern/kernel.img obj/fs/fs.img'
    )
    cmd = [
        "docker", "run", "--platform", "linux/amd64", "--rm",
        "-v", f"{LAB}:/lab", "-w", "/lab", "ubuntu:18.04",
        "bash", "-c", f"{DOCKER_SETUP} && {make_flags}",
    ]
    print(f"  building {test}...")
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
            if stop_on and re.search(stop_on, output.decode("utf-8", errors="replace")):
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    os.chdir(LAB)
    subprocess.run(["pkill", "-9", "qemu-system-i386"], stderr=subprocess.DEVNULL)
    time.sleep(1)

    ok = 0
    total = 0

    def check(name, passed):
        nonlocal ok, total
        total += 1
        print(f"{name}: {'OK' if passed else 'FAIL'}")
        if passed:
            ok += 1

    if not args.no_build:
        docker_build("user_pingpongsfork")
    out = run_qemu(45, stop_on=r"got 10 from")
    check("sfork pingpong", "got 10 from" in out and "thisenv" in out)

    if not args.no_build:
        docker_build("user_exectest")
    out = run_qemu(30)
    m = re.search(r"before exec envid=([0-9a-f]+).*i am environment \1", out, re.S)
    check("Unix exec", m is not None)

    print(f"Score: {ok}/{total}")
    sys.exit(0 if ok == total else 1)


if __name__ == "__main__":
    main()
