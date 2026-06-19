from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import *
import os

PersonBase = declarative_base()
TransferBase = declarative_base()
AuthBase = declarative_base()
ZoobarsBase = declarative_base()

class Person(PersonBase):
    __tablename__ = "person"
    username = Column(String(128), primary_key=True)
    profile = Column(String(5000), nullable=False, default="")

class Zoobars(ZoobarsBase):
    __tablename__ = "zoobars"
    username = Column(String(128), primary_key=True)
    zoobars = Column(Integer, nullable=False, default=10)

class Transfer(TransferBase):
    __tablename__ = "transfer"
    id = Column(Integer, primary_key=True)
    sender = Column(String(128))
    recipient = Column(String(128))
    amount = Column(Integer)
    time = Column(String)

class Auth(AuthBase):
    __tablename__ = "auth"
    username = Column(String(128), primary_key=True)
    password = Column(String(128))
    salt = Column(String(128))
    token = Column(String(128))

def dbsetup(name, base):
    thisdir = os.path.dirname(os.path.abspath(__file__))
    dbdir = os.path.join(thisdir, "db", name)
    if not os.path.exists(dbdir):
        os.makedirs(dbdir)

    dbfile = os.path.join(dbdir, "%s.db" % name)
    engine = create_engine('sqlite:///%s' % dbfile,
                           isolation_level='SERIALIZABLE')
    base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)
    return session()

def person_setup():
    return dbsetup("person", PersonBase)

def transfer_setup():
    return dbsetup("transfer", TransferBase)

def auth_setup():
    return dbsetup("auth", AuthBase)

def zoobars_setup():
    return dbsetup("zoobars", ZoobarsBase)

import sys
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s [init-person|init-transfer|init-auth|init-zoobars]" % sys.argv[0]
        exit(1)

    cmd = sys.argv[1]
    if cmd == 'init-person':
        person_setup()
    elif cmd == 'init-transfer':
        transfer_setup()
    elif cmd == 'init-auth':
        auth_setup()
    elif cmd == 'init-zoobars':
        zoobars_setup()
    else:
        raise Exception("unknown command %s" % cmd)
