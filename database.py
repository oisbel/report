from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	nombre = Column(String(250), nullable = False)
	email = Column(String(250), nullable = False)
	grado = Column(String(250))
	ministerio = Column(String(250))
	responsabilidad = Column(String(250))
	lugar = Column(String(250), nullable = False)
	pastor = Column(String(250))

class Report
	__tablename__ = "report"

	id = Column(Integer, primary_key = True)
	fecha = Column(DateTime, default=datetime.datetime.utcnow)
	avivamientos = Column(Integer)
	hogares = Column(Integer)
	estudios_establecidos = Column(Integer)
	estudios_realizados = Column(Integer)
	estudios_asistidos = Column(Integer)
	biblias = Column(Integer)
	mensajeros = Column(Integer)
	porciones = Column(Integer)
	visitas = Column(Integer)
	ayunos = Column(Integer)
	horas_ayunos = Column(Integer)
	enfermos = Column(Integer)
	sanidades = Column(Integer)
	mensajes = Column(Integer)
	cultos = Column(Integer)
	devocionales = Column(Integer)
	otros = Column(Integer)
	user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

class Biblical
	"""Estudio Biblico"""
	__tablename__ = "biblical"

	id = Column(Integer, primary_key = True)
	nombre = Column(String(250))
	init_fecha = Column(DateTime, default=datetime.datetime.utcnow)
	direccion = Column(String(250), nullable = False)
	user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User) # El que creo el estudio biblico
