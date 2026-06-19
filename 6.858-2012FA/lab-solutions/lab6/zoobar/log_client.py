import rpclib

def add_log(sender, recipient, zoobars):
    with rpclib.client_connect('/logsvc/sock') as c:
        return c.call('add_log', sender=sender, recipient=recipient,
                      zoobars=zoobars)

def get_log(username):
    with rpclib.client_connect('/logsvc/sock') as c:
        return c.call('get_log', username=username)
