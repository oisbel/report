from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	name = Column(String(250), nullable = False)
	email = Column(String(250), nullable = False)
	grado = Column(String(250))
	ministerio = Column(String(250))
	responsabilidad = Column(String(250))
	lugar = Column(String(250))
	pastor = Column(String(250))