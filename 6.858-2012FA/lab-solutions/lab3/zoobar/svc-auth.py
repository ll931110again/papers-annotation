#!/usr/bin/python

import rpclib
import auth_svc

class AuthRpcServer(rpclib.RpcServer):
    def rpc_login(self, username, password):
        return auth_svc.login(username, password)

    def rpc_register(self, username, password):
        return auth_svc.register(username, password)

    def rpc_check_token(self, username, token):
        return auth_svc.check_token(username, token)

AuthRpcServer().run_stdio()
