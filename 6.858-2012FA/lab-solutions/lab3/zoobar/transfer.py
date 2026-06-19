from flask import g, render_template, request

from login import requirelogin
from debug import *
import xfer_client

@catch_err
@requirelogin
def transfer():
    warning = None
    try:
        if 'recipient' in request.form:
            recipient = request.form['recipient']
            zoobars = int(request.form['zoobars'])
            if zoobars < 0:
                raise ValueError()
            if recipient == g.user.person.username:
                raise ValueError()
            xfer_client.transfer(g.user.person.username, recipient, zoobars)
            g.user.person.zoobars = xfer_client.balance(g.user.person.username)
            warning = "Sent %d zoobars" % zoobars
    except (KeyError, ValueError, AttributeError, TypeError) as e:
        log("Transfer exception: %s" % str(e))
        warning = "Transfer to %s failed" % request.form.get('recipient', '')

    return render_template('transfer.html', warning=warning)
