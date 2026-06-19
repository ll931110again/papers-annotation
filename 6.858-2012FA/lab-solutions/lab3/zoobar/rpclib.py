import os
import sys
import socket
import stat
import errno

import json

def parse_req(req):
    return json.loads(req)

def format_req(method, kwargs):
    return json.dumps([method, kwargs])

def parse_resp(resp):
    return json.loads(resp)

def format_resp(resp):
    return json.dumps(resp)

def buffered_readlines(sock):
    buf = ''
    while True:
        while '\n' in buf:
            (line, nl, buf) = buf.partition('\n')
            yield line
        try:
            newdata = sock.recv(4096)
            if newdata == '':
                break
            buf += newdata
        except IOError, e:
            if e.errno == errno.ECONNRESET:
                break

class RpcServer(object):
    def run_sock(self, sock):
        lines = buffered_readlines(sock)
        for req in lines:
            (method, kwargs) = parse_req(req)
            m = self.__getattribute__('rpc_' + method)
            ret = m(**kwargs)
            sock.sendall(format_resp(ret) + '\n')

    def run_stdio(self):
        buf = ''
        while True:
            while '\n' in buf:
                (line, nl, buf) = buf.partition('\n')
                (method, kwargs) = parse_req(line)
                m = self.__getattribute__('rpc_' + method)
                ret = m(**kwargs)
                os.write(1, format_resp(ret) + '\n')
            chunk = os.read(0, 4096)
            if chunk == '':
                break
            buf += chunk

class RpcClient(object):
    def __init__(self, sock):
        self.sock = sock
        self.lines = buffered_readlines(sock)

    def call(self, method, **kwargs):
        self.sock.sendall(format_req(method, kwargs) + '\n')
        return parse_resp(self.lines.next())

    def close(self):
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

def client_connect(pathname):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(pathname)
    return RpcClient(sock)
