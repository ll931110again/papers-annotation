from zoodb import *
import hashlib
import random
import os
import pbkdf2

def newtoken(db, cred):
    hashinput = "%s%.10f" % (cred.password, random.random())
    cred.token = hashlib.md5(hashinput).hexdigest()
    db.commit()
    return cred.token

def login(username, password):
    persondb = person_setup()
    if not persondb.query(Person).get(username):
        return None
    db_auth = auth_setup()
    cred = db_auth.query(Auth).get(username)
    if not cred:
        return None
    password = pbkdf2.PBKDF2(password, cred.salt).hexread(32)
    if cred.password == password:
        return newtoken(db_auth, cred)
    return None

def register(username, password):
    persondb = person_setup()
    if persondb.query(Person).get(username):
        return None

    newperson = Person()
    newperson.username = username
    persondb.add(newperson)
    persondb.commit()

    salt = os.urandom(32).encode('hex')
    password = pbkdf2.PBKDF2(password, salt).hexread(32)

    db_auth = auth_setup()
    newcred = Auth()
    newcred.username = username
    newcred.password = password
    newcred.salt = salt
    db_auth.add(newcred)
    db_auth.commit()
    return newtoken(db_auth, newcred)

def check_token(username, token):
    db = auth_setup()
    cred = db.query(Auth).get(username)
    return cred is not None and cred.token == token
