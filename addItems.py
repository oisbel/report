import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, User, Report, Biblical

engine = create_engine('sqlite:///report.db')
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
       grado="Buen Samaritano", lugar="Kingwood", pastor="Eddy Estrada")
session.add(user1)
session.commit()

# Reportes for user1
date0 = datetime.date(1943,3, 13)  #year, month, day
report0 = Report(
       fecha=date0,
       avivamientos=1,
       estudios_establecidos=1,
       ayunos=4,
       horas_ayunos=72,
       mensajes=2,
       cultos=1,
       user=user1)

session.add(report0)
session.commit()

date1 = datetime.date.today()
report1 = Report(
       fecha=date1,
       avivamientos=1,
       estudios_asistidos=1,
       ayunos=4,
       horas_ayunos=72,
       mensajes=1,
       cultos=1,
       user=user1)

session.add(report1)
session.commit()

# Biblical create for user1

init_date0 = datetime.date(1943,3, 10)
biblical0 = Biblical(
       nombre="Casa Porter",
       init_fecha=init_date0,
       direccion="24386 W Terrace Dr Porter 77365 TX",
       user=user1)

session.add(biblical0)
session.commit()

print "Added Items!"
