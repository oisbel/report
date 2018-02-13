import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# for generate password hash
from passlib.apps import custom_app_context as pwd_context

Base = declarative_base()


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	nombre = Column(String(250), nullable = False)
	email = Column(String(250), nullable = False)
	grado = Column(String(250), default = 'Miembro')
	ministerio = Column(String(250), default = '')
	responsabilidad = Column(String(250), default = '')
	lugar = Column(String(250), nullable = False)
	pastor = Column(String(250), default = '')
	password_hash = Column(String(64))

	def hash_password(self, password):
		""" Crea y almacena el password encriptado"""
		self.password_hash = pwd_context.encrypt(password)

	def verify_password(self, password):
		return pwd_context.verify(password, self.password_hash)

	@property
	def serialize(self):
		"""Return user data in easily serializeable format"""
		return {
			'id': self.id,
			'nombre': self.nombre,
			'email': self.email,
			'grado': self.grado,
			'ministerio': self.ministerio,
			'responsabilidad': self.responsabilidad,
			'lugar': self.lugar,
			'pastor': self.pastor,
		}


class Report(Base):
	__tablename__ = "report"

	id = Column(Integer, primary_key = True)
	fecha = Column(DateTime, default=datetime.datetime.utcnow)
	avivamientos = Column(Integer, default = 0)
	hogares = Column(Integer, default = 0)
	estudios_establecidos = Column(Integer, default = 0)
	estudios_realizados = Column(Integer, default = 0)
	estudios_asistidos = Column(Integer, default = 0)
	biblias = Column(Integer, default = 0)
	mensajeros = Column(Integer, default = 0)
	porciones = Column(Integer, default = 0)
	visitas = Column(Integer, default = 0)
	ayunos = Column(Integer, default = 0)
	horas_ayunos = Column(Integer, default = 0)
	enfermos = Column(Integer, default = 0)
	sanidades = Column(Integer, default = 0)
	mensajes = Column(Integer, default = 0)
	cultos = Column(Integer, default = 0)
	devocionales = Column(Integer, default = 0)
	otros = Column(String(250), default = '')
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	@property
	def serialize(self):
		"""Return report data in easily serializeable format"""
		return {
			'user_id': self.user_id,
			'id': self.id,
			'fecha': self.fecha,
			'avivamientos': self.avivamientos,
			'hogares': self.hogares,
			'estudios_establecidos': self.estudios_establecidos,
			'estudios_realizados': self.estudios_realizados,
			'estudios_asistidos': self.estudios_asistidos,
			'biblias': self.biblias,
			'mensajeros': self.mensajeros,
			'porciones': self.porciones,
			'visitas': self.visitas,
			'ayunos': self.ayunos,
			'horas_ayunos': self.horas_ayunos,
			'enfermos': self.enfermos,
			'sanidades': self.sanidades,
			'mensajes': self.mensajes,
			'cultos': self.cultos,
			'devocionales': self.devocionales,
			'otros': self.otros,
		}

class Biblical(Base):
	"""Estudio Biblico"""
	__tablename__ = "biblical"

	id = Column(Integer, primary_key = True)
	nombre = Column(String(250))
	init_fecha = Column(DateTime, default=datetime.datetime.utcnow)
	direccion = Column(String(250), nullable = False)
	user_id = Column(Integer, ForeignKey('user.id'))
	user = relationship(User) # El que creo el estudio biblico

	@property
	def serialize(self):
		"""Return biblical data in easily serializeable format"""
		return {
			'user_id': self.user_id,
			'id': self.id,
			'nombre': self.nombre,
			'init_fecha': self.init_fecha,
			'direccion': self.direccion,
		}


engine = create_engine('sqlite:///report.db')

Base.metadata.create_all(engine)
