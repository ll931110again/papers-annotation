#!/usr/bin/env python3
"""Run lab6 grade checks on the host (build in Docker, QEMU on macOS)."""

import argparse
import os
import re
import select
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error

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


def gdb_port():
    uid = os.getuid()
    return uid % 5000 + 25000


def echo_port():
    return gdb_port() + 1


def http_port():
    return gdb_port() + 2


def docker_build(test, extra_make="", no_ns=True):
    init = f'-DTEST_NO_NS -DTEST={test}' if no_ns else f'-DTEST={test}'
    make_flags = (
        f'make {extra_make} "INIT_CFLAGS={init}" '
        f'obj/kern/kernel.img obj/fs/fs.img'
    )
    cmd = [
        "docker", "run", "--platform", "linux/amd64", "--rm",
        "-v", f"{LAB}:/lab", "-w", "/lab", "ubuntu:18.04",
        "bash", "-c", f"{DOCKER_SETUP} && {make_flags}",
    ]
    print(f"  building {test}...")
    subprocess.run(cmd, check=True)


def run_qemu(timeout=60, stop_on=None, net=True, on_line=None, stop_event=None):
    qemu = qemu_path()
    cmd = [
        qemu, "-nographic",
        "-drive", "file=obj/kern/kernel.img,format=raw,if=ide",
        "-drive", "file=obj/fs/fs.img,format=raw,if=ide",
        "-serial", "mon:stdio",
    ]
    if net:
        p7, p80 = echo_port(), http_port()
        hostfwd = (
            f"hostfwd=tcp:127.0.0.1:{p7}-:7,"
            f"hostfwd=tcp:127.0.0.1:{p80}-:80,"
            f"hostfwd=udp:127.0.0.1:{p7}-:7"
        )
        cmd += [
            "-netdev", f"user,id=net0,{hostfwd}",
            "-device", "e1000,netdev=net0",
        ]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, cwd=LAB)
    output = b""
    start = time.time()
    fd = proc.stdout.fileno()
    fired = set()
    while time.time() - start < timeout:
        if stop_event and stop_event.is_set():
            break
        ready, _, _ = select.select([fd], [], [], 0.2)
        if ready:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            output += chunk
            text = output.decode("utf-8", errors="replace")
            if on_line:
                for pattern, cb in on_line.items():
                    if pattern not in fired and re.search(pattern, text):
                        fired.add(pattern)
                        cb()
            if stop_on and re.search(stop_on, text):
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


def testinput_final(count):
    digits = tuple("%03d" % (count - 1))
    return "input: 0030   203%s 3%s3%s" % digits


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-build", action="store_true")
    args = parser.parse_args()
    os.chdir(LAB)
    subprocess.run(["pkill", "-9", "qemu-system-i386"], stderr=subprocess.DEVNULL)
    time.sleep(1)

    score = 0
    total = 105

    def check(name, points, ok, detail=""):
        nonlocal score
        print(f"{name}: {'OK' if ok else 'FAIL'}")
        if detail and not ok:
            print(f"    {detail}")
        if ok:
            score += points

    # Part A
    if not args.no_build:
        docker_build("user_testtime")
    out = run_qemu(30, net=False)
    check("testtime", 5, bool(re.search(r"starting count down: 5 4 3 2 1 0", out)))

    if not args.no_build:
        docker_build("user_hello")
    out = run_qemu(30, net=False)
    check("pci attach", 5, "8086:100e" in out and "enabled" in out)

    if not args.no_build:
        docker_build("net_testoutput", 'NET_CFLAGS=-DTESTOUTPUT_COUNT=5')
    out = run_qemu(45, stop_on=r"Transmitting packet 4\n")
    check("testoutput [5]", 15, out.count("Transmitting packet") >= 5)

    if not args.no_build:
        docker_build("net_testoutput", 'NET_CFLAGS=-DTESTOUTPUT_COUNT=100')
    out = run_qemu(90, stop_on=r"Transmitting packet 99\n")
    check("testoutput [100]", 10, out.count("Transmitting packet") >= 100)

    print("=== Part A score: min(35, %d) ===" % min(35, score))

    # Part B - testinput
    if not args.no_build:
        docker_build("net_testinput")

    for label, count, points in [("[5]", 5, 15), ("[100]", 100, 10)]:
        send_thread = [None]

        def start_send():
            def send_udp():
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                try:
                    sock.connect(("127.0.0.1", echo_port()))
                    for i in range(count):
                        sock.send(("Packet %03d" % i).encode())
                finally:
                    sock.close()

            send_thread[0] = threading.Thread(target=send_udp, daemon=True)
            send_thread[0].start()

        final = testinput_final(count)
        out = run_qemu(
            120,
            stop_on=re.escape(final),
            on_line={"Waiting for packets": start_send},
        )
        if send_thread[0]:
            send_thread[0].join(timeout=10)
        ok = final in out
        check(f"testinput {label}", points, ok)

    # echosrv
    if not args.no_build:
        docker_build("user_echosrv", no_ns=False)
    expect = f"{time.time()}: network server works"
    got_holder = [""]
    stop = threading.Event()

    def try_echo():
        sock = socket.socket()
        try:
            sock.settimeout(10)
            sock.connect(("127.0.0.1", echo_port()))
            sock.sendall(expect.encode())
            data = b""
            while len(data) < len(expect):
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            got_holder[0] = data.decode("utf-8", errors="replace")
        except OSError as e:
            got_holder[0] = f"[Socket error: {e}]"
        finally:
            try:
                sock.close()
            except Exception:
                pass
        if got_holder[0] == expect:
            stop.set()

    run_qemu(60, on_line={"bound": try_echo}, stop_event=stop)
    check("echosrv", 15, got_holder[0] == expect, f"got {got_holder[0]!r}")

    # httpd
    if not args.no_build:
        docker_build("user_httpd", no_ns=False)
    http_ok = [False]
    stop = threading.Event()

    def try_http():
        try:
            url = f"http://127.0.0.1:{http_port()}/index.html"
            with urllib.request.urlopen(url, timeout=10) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            http_ok[0] = "This file came from JOS" in body
        except Exception:
            http_ok[0] = False
        if http_ok[0]:
            stop.set()

    run_qemu(60, on_line={"Waiting for http connections": try_http}, stop_event=stop)
    check("httpd /index.html", 10, http_ok[0])

    for path, code, body in [
        ("/", 404, "404"),
        ("/random_file.txt", 404, "404"),
    ]:
        http_ok = [False]
        stop = threading.Event()

        def try_http_path(p=path, c=code, b=body):
            def run():
                try:
                    url = f"http://127.0.0.1:{http_port()}{p}"
                    with urllib.request.urlopen(url, timeout=10) as resp:
                        got = resp.status
                        text = resp.read().decode("utf-8", errors="replace")
                except urllib.error.HTTPError as e:
                    got = e.code
                    text = e.read().decode("utf-8", errors="replace")
                except Exception:
                    got = 0
                    text = ""
                http_ok[0] = got == c and (b in text)
                if http_ok[0]:
                    stop.set()
            threading.Thread(target=run, daemon=True).start()

        if not args.no_build:
            docker_build("user_httpd", no_ns=False)

        def start_http():
            try_http_path()

        run_qemu(60, on_line={"Waiting for http connections": start_http}, stop_event=stop)
        check(f"httpd {path}", 10, http_ok[0])

    print(f"Score: {score}/{total}")
    sys.exit(0 if score >= 95 else 1)


if __name__ == "__main__":
    main()
