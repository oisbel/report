# coding=utf-8

import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, Member, Report, Biblical, Church, Statistic

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

session.query(Report).delete()

print("Eliminada contenido tabla reportes!")

session.query(Member).filter_by(admin=False).delete()

print("Usuarios regulares eliminados")

session.query(Statistic).delete()

print("Estadisticas de reportes por mes eliminada")

session.commit()
