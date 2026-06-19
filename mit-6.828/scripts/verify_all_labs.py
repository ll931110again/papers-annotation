#!/usr/bin/env python3
"""Build per-lab test kernels and run all graders."""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = os.path.join(ROOT, "lab")

DOCKER_SETUP = (
    "apt-get update -qq && "
    "DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gcc-multilib make binutils >/dev/null && "
    'printf "GCCPREFIX=\\nQEMU=qemu-system-i386\\nCFLAGS += -std=gnu99 -fno-pic -no-pie\\n" > conf/env.mk'
)


def docker_make(target):
    cmd = [
        "docker", "run", "--platform", "linux/amd64", "--rm",
        "-v", f"{LAB}:/lab", "-w", "/lab", "ubuntu:18.04",
        "bash", "-c", f"{DOCKER_SETUP} && {target}",
    ]
    print(f"  docker: {target}")
    subprocess.run(cmd, check=True)


def run(script, *args):
    subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", script), *args],
        cwd=ROOT, check=False,
    )


def main():
    subprocess.run(["pkill", "-9", "qemu-system-i386"], stderr=subprocess.DEVNULL)
    results = {}

    print("=== Lab 1 ===")
    docker_make("make obj/kern/kernel.img")
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "grade_lab1.py"), "--no-build"],
        cwd=ROOT)
    results[1] = r.returncode == 0

    print("\n=== Lab 2 ===")
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "grade_lab.py"), "2", "--no-build"],
        cwd=ROOT)
    results[2] = r.returncode == 0

    print("\n=== Lab 3 ===")
    docker_make('make "INIT_CFLAGS=-DTEST=user_hello" obj/kern/kernel.img')
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "grade_lab.py"), "3", "--no-build"],
        cwd=ROOT)
    results[3] = r.returncode == 0

    print("\n=== Lab 4 ===")
    docker_make('make "INIT_CFLAGS=-DTEST=user_primes" obj/kern/kernel.img')
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "grade_lab.py"), "4", "--no-build"],
        cwd=ROOT)
    results[4] = r.returncode == 0

    print("\n=== Lab 5 (smoke) ===")
    docker_make("make obj/kern/kernel.img obj/fs/fs.img")
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "grade_lab.py"), "5", "--no-build"],
        cwd=ROOT)
    results["5-smoke"] = r.returncode == 0

    print("\n=== Lab 5 (full) ===")
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "grade_lab5.py")],
        cwd=ROOT)
    results["5-full"] = r.returncode == 0

    print("\n=== Lab 6 ===")
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "grade_lab6.py")],
        cwd=ROOT)
    results[6] = r.returncode == 0

    print("\n=== Summary ===")
    all_ok = True
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"Lab {name}: {status}")
        all_ok = all_ok and ok

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
