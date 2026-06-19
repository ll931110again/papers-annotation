#!/usr/bin/python

import rpclib
import xfer

class XferRpcServer(rpclib.RpcServer):
    def rpc_transfer(self, sender, recipient, zoobars):
        return xfer.transfer(sender, recipient, zoobars)

    def rpc_balance(self, username):
        return xfer.balance(username)

    def rpc_check_in(self, username):
        xfer.check_in(username)
        return True

    def rpc_get_log(self, username):
        return xfer.get_log(username)

XferRpcServer().run_stdio()
