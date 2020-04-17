# coding=utf-8

import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, User, Report, Biblical, Church, Statistic

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

church0 = Church(
       nombre="Kingwood", pais="E.U. Oeste",
       direccion="201 Sorters Mc Clellan, Kingwood TX 77339",
       pastor="Eddy Estrada")

session.add(church0)

church1 = Church(
       nombre="Miami", pais ="E.U. Sur",
       direccion="660 W Flagler St, Miami FL 33130",
       pastor="David Lopez")

session.add(church1)

print("Added 2 main churchs: Kingwood and Miami")

# Create users
user1 = User(nombre="Kingwood-Admin", email="admin1@sccristo.org", admin=True, church=church0)
user1.hash_password('Soldados2020-1')
session.add(user1)

user2 = User(nombre="Miami-Admin", email="admin2@sccristo.org", admin=True, church=church1)
user2.hash_password('Soldados2020-2')
session.add(user2)

print("Added 2 admin users for Miami and Kingwood!")

filepath='Iglesias.txt'
file = io.open(filepath,encoding='utf-8')
count = 3

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

print("Added Churchs from file!")

user3 = User(nombre="Soldados de la Cruz de Cristo", email="scruzcristo@gmail.com",
       admin=True, super_admin=True, church=church1)
user3.hash_password('Reportes_19')
session.add(user3)

print("Added super_admin!")

session.commit()
