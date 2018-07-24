# coding=utf-8

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, Church

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
       nombre="Houston",
       direccion="201 Sorters Mc Clellan, Kingwood 77339 TX",
       feligresia=200,
       estudios_biblicos=30,
       pastor="Eddy Estrada")

session.add(church0)
session.commit()

church1 = Church(
       nombre="Miami",
       direccion="660 W Flagler St, Miami, FL 33130",
       feligresia=100,
       estudios_biblicos=3,
       pastor="David Lopez")

session.add(church1)
session.commit()

church2 = Church(
       nombre="Tampa",
       direccion= u'Armínia',
       feligresia=200,
       pastor="Sergio Gonzalez")

session.add(church2)
session.commit()

print "Added Churchs!"