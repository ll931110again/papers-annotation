import sys, json, os

def parse_kv(argv):
    kv = {}
    for arg in argv:
        pos = arg.find('=')
        if pos < 0:
            continue
        kv[arg[:pos]] = arg[pos + 1:]
    return kv

def get_param(key):
    return parse_kv(sys.argv).get(key)

def _rpc(method, **kwargs):
    fd = os.open('/svc/xfer', os.O_RDWR)
    req = json.dumps([method, kwargs]) + '\n'
    os.write(fd, req)
    buf = ''
    while '\n' not in buf:
        chunk = os.read(fd, 4096)
        if not chunk:
            break
        buf += chunk
    os.close(fd)
    return json.loads(buf.split('\n', 1)[0])

def get_xfers(username):
    return _rpc('get_log', username=username)

def get_user(username):
    return _rpc('get_user', username=username)

def xfer(rcptname, zoobars):
    selfname = get_param('ZOOBAR_SELF')
    return _rpc('transfer', sender=selfname, recipient=rcptname,
                 zoobars=zoobars)
