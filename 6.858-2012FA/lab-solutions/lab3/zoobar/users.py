from flask import g, render_template, request, Markup

from login import requirelogin
from zoodb import *
from debug import *
from profile import *
import xfer_client

@catch_err
@requirelogin
def users():
    args = {}
    args['req_user'] = Markup(request.args.get('user', ''))
    if 'user' in request.values:
        user = g.persondb.query(Person).get(request.values['user'])
        if user:
            if user.profile.startswith("#!python"):
                p = run_profile(user)
            else:
                p = user.profile
            args['profile'] = Markup("<b>%s</b>" % p)
            args['user'] = user
            user.zoobars = xfer_client.balance(user.username)
            args['transfers'] = xfer_client.get_log(user.username)
        else:
            args['warning'] = "Cannot find that user."
    return render_template('users.html', **args)
