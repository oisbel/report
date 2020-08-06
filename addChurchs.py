# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, Church, User

import io
engine = create_engine('sqlite:///report.db')
# engine = create_engine('postgresql://report:vryyo@localhost/report')

# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Churchs create

# Agregar las jugadas
filepath='Iglesias.txt'
file = io.open(filepath,encoding='utf-8')
count = 4

for line in file:
       l=line.split('-',1)
       church=Church(nombre=l[1], pais=l[0])
       session.add(church)
       name = l[1] + ' - Admin'
       email = "admin{}@sccristo.org".format(str(count))
       user = User(nombre=name , email=email, admin=True, church=church)
       password = "Soldados2020-{}".format(str(count))
       user.hash_password(password)
       print(email)
       print(password)
       count = count + 1
       session.add(user)

file.close()

session.commit()

print "Added Churchs!"