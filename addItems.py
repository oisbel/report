# coding=utf-8

import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, User, Report, Biblical, Church, Statistic

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
       nombre="Kingwood(Houston)",
       direccion="201 Sorters Mc Clellan, Kingwood 77339 TX",
       feligresia=1,
       estudios_biblicos=0,
       pastor="Eddy Estrada")

session.add(church0)
#session.commit()

church1 = Church(
       nombre="Miami",
       direccion="660 W Flagler St, Miami, FL 33130",
       feligresia=0,
       estudios_biblicos=0,
       pastor="David Lopez")

session.add(church1)
#session.commit()

print "Added Churchs!"

# Create users
user1 = User(nombre="Oisbel Simpson", email="oisbelsimpv@gmail.com",
       grado="Buen Samaritano", admin=True, church=church0)
user1.hash_password('vryyo')
session.add(user1)
#session.commit()

user2 = User(nombre="Soldados de la Cruz de Cristo", email="scruzcristo@gmail.com",
       admin=True, super_admin=True, church=church1)
user2.hash_password('Reportes_19')
session.add(user2)
#session.commit()

# Reportes for user1
date0 = datetime.date(2020,1, 25)  #year, month, day
report0 = Report(
       fecha=date0,
       year=2020,
       month=1,
       day=25,
       avivamientos=1,
       ayunos=4,
       horas_ayunos=72,
       mensajes=1,
       user=user1)

session.add(report0)
#session.commit()

statistic = Statistic(month=1, reports_count=1)
session.add(statistic)
session.commit()

# Biblical create for user1

#init_date0 = datetime.date(2017,3, 10)
#biblical0 = Biblical(
#       nombre= u'Casa Pórter',
#       init_fecha=init_date0,
#       year=2017,
#       month=3,
#       day=10,
#       direccion="24386 W Terrace Dr Porter 77365 TX",
#       user=user1)

#session.add(biblical0)
#session.commit()

print "Added Items!"
