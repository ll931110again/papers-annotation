from zoodb import *
import time

def add_log(sender, recipient, zoobars):
    transferdb = transfer_setup()
    transfer = Transfer()
    transfer.sender = sender
    transfer.recipient = recipient
    transfer.amount = zoobars
    transfer.time = time.asctime()
    transferdb.add(transfer)
    transferdb.commit()

def get_log(username):
    db = transfer_setup()
    ret = db.query(Transfer).filter(or_(Transfer.sender == username,
                                        Transfer.recipient == username))
    retlist = []
    for item in ret:
        retlist.append({
            'time': item.time,
            'sender': item.sender,
            'recipient': item.recipient,
            'amount': item.amount,
        })
    return retlist
