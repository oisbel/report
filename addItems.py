import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, User, Report, Biblical

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


# Create user
user1 = User(nombre="Oisbel Simpson", email="oisbelsimpv@gmail.com",
       grado="Buen Samaritano", lugar="Kingwood", pastor="Eddy Estrada", numero=7)
user1.hash_password('vryyo')
session.add(user1)
session.commit()

# Reportes for user1
date0 = datetime.date(2018,1, 25)  #year, month, day
report0 = Report(
       fecha=date0,
       year=2018,
       month=1,
       day=25,
       avivamientos=1,
       estudios_establecidos=1,
       ayunos=4,
       horas_ayunos=72,
       mensajes=2,
       cultos=1,
       horas_trabajo=4,
       user=user1)

session.add(report0)
session.commit()

# Biblical create for user1

init_date0 = datetime.date(2017,3, 10)
biblical0 = Biblical(
       nombre="Casa Porter",
       init_fecha=init_date0,
       year=2017,
       month=3,
       day=10,
       direccion="24386 W Terrace Dr Porter 77365 TX",
       user=user1)

session.add(biblical0)
session.commit()

print "Added Items!"
