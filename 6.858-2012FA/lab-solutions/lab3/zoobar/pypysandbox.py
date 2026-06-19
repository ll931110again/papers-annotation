import os, sys, errno, re
from cStringIO import StringIO

pypy_sandbox_dir = '/zoobar/pypy-sandbox'
sys.path = [pypy_sandbox_dir] + sys.path

from pypy.translator.sandbox import pypy_interact, sandlib, vfs
from pypy.translator.sandbox.vfs import Dir, RealDir, RealFile
from pypy.rpython.module.ll_os_stat import s_StatResult
from pypy.tool.lib_pypy import LIB_ROOT

def safe_username(name):
    return re.sub(r'[^\w@\-]', '_', name)

class WritableFile(object):
    def __init__(self, path):
        if hasattr(path, 'path'):
            self.path = path.path
        else:
            self.path = path

    def open(self):
        parent = os.path.dirname(self.path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, 0700)
        return open(self.path, 'w+b')

class UnixSocketNode(object):
    def __init__(self, sockpath):
        self.sockpath = sockpath

    def open(self):
        import socket
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(self.sockpath)
        return s

class MySandboxedProc(pypy_interact.PyPySandboxedProc):
    def __init__(self, profile_owner, code, args):
        self.profile_owner = profile_owner
        self.usertmp = os.path.join('/tmp/sandbox-root',
                                    safe_username(profile_owner))
        if not os.path.exists(self.usertmp):
            os.makedirs(self.usertmp, 0700)
        super(MySandboxedProc, self).__init__(
            pypy_sandbox_dir + '/pypy/translator/goal/pypy-c',
            ['-S', '-c', code] + args
        )
        self.debug = False
        self.virtual_cwd = '/'

    def tmp_real_path(self, vpathname):
        if vpathname == '/tmp':
            return self.usertmp
        if not vpathname.startswith('/tmp/'):
            return None
        rest = vpathname[5:]
        parts = []
        for part in rest.split('/'):
            if part in ('', '.'):
                continue
            if part == '..':
                raise OSError(errno.EACCES)
            parts.append(part)
        if not parts:
            return self.usertmp
        return os.path.join(self.usertmp, *parts)

    def is_tmp_path(self, vpathname):
        return vpathname == '/tmp' or vpathname.startswith('/tmp/')

    def get_node(self, vpath):
        if vpath == '/svc/xfer':
            return UnixSocketNode('/xfersvc/sock')
        dirnode, name = self.translate_path(vpath)
        if name:
            node = dirnode.join(name)
        else:
            node = dirnode
        if self.debug:
            sandlib.log.vpath('%r => %r' % (vpath, node))
        return node

    def handle_message(self, fnname, *args):
        if '__' in fnname:
            raise ValueError("unsafe fnname")
        try:
            handler = getattr(self, 'do_' + fnname.replace('.', '__'))
        except AttributeError:
            raise RuntimeError("no handler for " + fnname)
        resulttype = getattr(handler, 'resulttype', None)
        return handler(*args), resulttype

    def build_virtual_root(self):
        exclude = ['.pyc', '.pyo']
        libroot = str(LIB_ROOT)

        return Dir({
            'bin': Dir({'pypy-c': RealFile(self.executable),
                        'lib-python': RealDir(libroot + '/lib-python',
                                              exclude=exclude),
                        'lib_pypy': RealDir(libroot + '/lib_pypy',
                                            exclude=exclude)}),
            'proc': Dir({'cpuinfo': RealFile('/proc/cpuinfo')}),
            'tmp': RealDir(self.usertmp, exclude=exclude),
            'zoobar': Dir({
                'proflib.py': RealFile('/zoobar/sandbox_proflib.py'),
            }),
            'svc': Dir({
                'xfer': UnixSocketNode('/xfersvc/sock'),
            }),
        })

    def do_ll_os__ll_os_geteuid(self):
        return 0

    def do_ll_os__ll_os_getuid(self):
        return 0

    def do_ll_os__ll_os_getegid(self):
        return 0

    def do_ll_os__ll_os_getgid(self):
        return 0

    def do_ll_os__ll_os_fstat(self, fd):
        f = self.get_file(fd)
        try:
            return os.fstat(f.fileno())
        except:
            raise OSError(errno.EINVAL)
    do_ll_os__ll_os_fstat.resulttype = s_StatResult

    def do_ll_os__ll_os_open(self, vpathname, flags, mode):
        if vpathname == '/svc/xfer':
            node = UnixSocketNode('/xfersvc/sock')
            f = node.open()
            return self.allocate_fd(f)

        write_flags = flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND |
                               os.O_CREAT | os.O_TRUNC)
        if write_flags:
            if not self.is_tmp_path(vpathname):
                raise OSError(errno.EPERM, "write access denied")
            realpath = self.tmp_real_path(vpathname)
            node = WritableFile(realpath)
            f = node.open()
            if flags & os.O_TRUNC:
                f.truncate(0)
            return self.allocate_fd(f)

        node = self.get_node(vpathname)
        f = node.open()
        return self.allocate_fd(f)

    def do_ll_os__ll_os_write(self, fd, data):
        try:
            f = self.get_file(fd)
            return os.write(f.fileno(), data)
        except:
            raise OSError(errno.EPERM, "write not implemented yet")

    def do_ll_os__ll_os_mkdir(self, vpathname, mode):
        if not self.is_tmp_path(vpathname):
            raise OSError(errno.EPERM)
        realpath = self.tmp_real_path(vpathname)
        os.makedirs(realpath, 0700)

    def do_ll_os__ll_os_rmdir(self, vpathname):
        if not self.is_tmp_path(vpathname):
            raise OSError(errno.EPERM)
        realpath = self.tmp_real_path(vpathname)
        os.rmdir(realpath)

    def do_ll_os__ll_os_rename(self, old, new):
        if not self.is_tmp_path(old) or not self.is_tmp_path(new):
            raise OSError(errno.EPERM)
        os.rename(self.tmp_real_path(old), self.tmp_real_path(new))

    def do_ll_os__ll_os_unlink(self, vpathname):
        if not self.is_tmp_path(vpathname):
            raise OSError(errno.EPERM)
        os.unlink(self.tmp_real_path(vpathname))

    def do_ll_os__ll_os_symlink(self, src, dst):
        if not self.is_tmp_path(dst):
            raise OSError(errno.EPERM)
        if self.is_tmp_path(src):
            src = self.tmp_real_path(src)
        else:
            if '..' in src.split('/'):
                raise OSError(errno.EPERM)
        os.symlink(src, self.tmp_real_path(dst))

def run(profile_owner, code, args=[], timeout=None):
    sandproc = MySandboxedProc(profile_owner, code, args)

    if timeout is not None:
        sandproc.settimeout(timeout, interrupt_main=True)
    try:
        code_output = StringIO()
        sandproc.interact(stdout=code_output, stderr=code_output)
        return code_output.getvalue()
    finally:
        sandproc.kill()
