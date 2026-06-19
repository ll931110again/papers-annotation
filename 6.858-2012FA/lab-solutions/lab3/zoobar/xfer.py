from zoodb import *
import log_client

def transfer(sender, recipient, zoobars):
    zoobarsdb = zoobars_setup()
    senderp = zoobarsdb.query(Zoobars).get(sender)
    recipientp = zoobarsdb.query(Zoobars).get(recipient)

    if not senderp or not recipientp:
        return None

    sender_balance = senderp.zoobars - zoobars
    recipient_balance = recipientp.zoobars + zoobars

    if sender_balance < 0 or recipient_balance < 0:
        raise ValueError()

    senderp.zoobars = sender_balance
    recipientp.zoobars = recipient_balance
    zoobarsdb.commit()

    log_client.add_log(sender, recipient, zoobars)
    return True

def check_in(username):
    zoobarsdb = zoobars_setup()
    user = zoobarsdb.query(Zoobars).get(username)
    if user:
        return

    acct = Zoobars()
    acct.username = username
    zoobarsdb.add(acct)
    zoobarsdb.commit()

def balance(username):
    db = zoobars_setup()
    acct = db.query(Zoobars).get(username)
    if not acct:
        return None
    return acct.zoobars

def get_log(username):
    return log_client.get_log(username)
