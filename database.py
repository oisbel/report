import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

# for generate password hash
from passlib.apps import custom_app_context as pwd_context
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))


class User(Base):
	__tablename__ = 'user'

	id = Column(Integer, primary_key = True)
	nombre = Column(String(250), nullable = False)
	email = Column(String(250), nullable = False)
	grado = Column(String(250), default = 'Miembro')
	ministerio = Column(String(250), default = '')
	responsabilidad = Column(String(250), default = '')
	lugar = Column(String(250), nullable = False)
	numero = Column(Integer, default = 0)
	pastor = Column(String(250), default = '')
	password_hash = Column(String(250))

	def hash_password(self, password):
		""" Crea y almacena el password encriptado"""
		self.password_hash = pwd_context.encrypt(password)

	def verify_password(self, password):
		return pwd_context.verify(password, self.password_hash)

	def generate_auth_token(self, expiration=3600):
		s = Serializer(secret_key, expires_in = expiration)
		return s.dumps({'id': self.id })

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(secret_key)
		try:
			data = s.loads(token)
		except SignatureExpired:
			#Valid Token, but expired
			return None
		except BadSignature:
			#Invalid Token
			return None
		user_id = data['id']
		return user_id

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
			'password': self.password_hash,
		}


class Report(Base):
	__tablename__ = "report"

	id = Column(Integer, primary_key = True)
	fecha = Column(DateTime, default=datetime.datetime.utcnow)
	year = Column(Integer, default = 0)
	month = Column(Integer, default = 0)
	day = Column(Integer, default = 0)
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
	horas_trabajo = Column(Integer, default = 0)
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
			'year': self.year,
			'month': self.month,
			'day': self.day,
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
			'horas_trabajo':self.horas_trabajo,
			'otros': self.otros
		}

class Biblical(Base):
	"""Estudio Biblico"""
	__tablename__ = "biblical"

	id = Column(Integer, primary_key = True)
	nombre = Column(String(250))
	init_fecha = Column(DateTime, default=datetime.datetime.utcnow)
	year = Column(Integer, default = 0)
	month = Column(Integer, default = 0)
	day = Column(Integer, default = 0)
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
			'year': self.year,
			'month': self.month,
			'day': self.day,
			'direccion': self.direccion
		}


engine = create_engine('sqlite:///report.db')
# engine = create_engine('postgresql://report:vryyo@localhost/report')

Base.metadata.create_all(engine)
