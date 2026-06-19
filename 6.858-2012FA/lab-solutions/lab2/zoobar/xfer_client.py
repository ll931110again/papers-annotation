import rpclib

def transfer(sender, recipient, zoobars):
    with rpclib.client_connect('/xfersvc/sock') as c:
        return c.call('transfer', sender=sender, recipient=recipient,
                      zoobars=zoobars)

def balance(username):
    with rpclib.client_connect('/xfersvc/sock') as c:
        return c.call('balance', username=username)

def check_in(username):
    with rpclib.client_connect('/xfersvc/sock') as c:
        return c.call('check_in', username=username)

def get_log(username):
    with rpclib.client_connect('/xfersvc/sock') as c:
        return c.call('get_log', username=username)
