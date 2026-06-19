#!/usr/bin/python

import rpclib
import log

class LogRpcServer(rpclib.RpcServer):
    def rpc_add_log(self, sender, recipient, zoobars):
        log.add_log(sender, recipient, zoobars)
        return True

    def rpc_get_log(self, username):
        return log.get_log(username)

LogRpcServer().run_stdio()
