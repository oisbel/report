import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
from flask import abort, g

# For database
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database import Base, User, Report, Biblical

# For anti-forgery
from flask import session as login_session
import random
import string

# to fix IO Error Broken Pipe
#from signal import signal, SIGPIPE, SIG_DFL
#signal(SIGPIPE,SIG_DFL) # no funciono porque en ves de darme el error apaga el servidor, al menos el local

# For auth token and password
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///report.db')
# engine = create_engine('postgresql://report:vryyo@localhost/report')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/')
def showMain():
       list = ["test1","test2","test3"]
       return render_template('reportes.html', list=list)

@auth.verify_password
def verify_password(username_or_token, password):
       """ Usado por HTTPBasicAuth para verificar
        que sea un usuario el que accede a las funciones con el decorador @auth.verify_password
        Se ha agregado un token para no tener que transmitir por la web el usurio y password """
       # Try to see if it's a token first
       user_id = User.verify_auth_token(username_or_token)
       if user_id:
              user = session.query(User).filter_by(id = user_id).one()
       else: # No es un token sino credenciales de usuario(siempre el email y password)
              try:
                     user = session.query(User).filter_by(email = username_or_token).one()
                     if not user or not user.verify_password(password):
                            return False
              except: #Era un token invalido
                     return False
       g.user = user
       return True

@app.route('/token')
@auth.login_required
def get_auth_token():
       """ Genera un token para el usuario dado en los parametros"""
       token = g.user.generate_auth_token()
       return jsonify({'token': token.decode('ascii')})

# JSON api to see if it is time to create a new report or just edit the last one
@app.route('/ask', methods = ['GET'])
@auth.login_required
def ItIsTimeToNewReport():
       """ Devuelve true si el ultimo reporte del usuario es de un mes distinto
       del actual"""
       actual_month = datetime.date.today().month

       result={'status':'ok'}
       user_id = request.args.get('user_id')
       try:
              user = session.query(User).filter_by(id=user_id).one()
              report = session.query(Report).filter_by(user_id=user.id).order_by(-Report.id).one()
              ask = {'ask':'no'}
              if(report.month != actual_month):
                     ask = {'ask':'yes'}
              result.update(ask)
       except:
              result['status'] = 'fail'
       return jsonify(Report=result)

@app.route('/adduser', methods = ['POST'])
def new_user():
       """ Crea un usuario"""
       nombre = request.json.get('nombre')
       email = request.json.get('email') # username es el email
       grado = request.json.get('grado')
       ministerio = request.json.get('ministerio')
       responsabilidad = request.json.get('responsabilidad')
       lugar = request.json.get('lugar')

       numero = request.json.get('numero', 0)

       pastor = request.json.get('pastor')
       password = request.json.get('password')

       if email is None or password is None or lugar is None or nombre is None:
              # print "missing arguments"
              abort(400)
       if session.query(User).filter_by(email = email).first() is not None:
              # print "existing user"
              return jsonify({'message':'user already exists'})#, 200

       user = User(nombre = nombre, email = email, grado = grado,
              ministerio = ministerio, responsabilidad =responsabilidad,
              lugar = lugar, pastor = pastor, numero = numero)
       user.hash_password(password)
       session.add(user)
       session.commit()
       return jsonify({ 'email': user.email , 'id': user.id})#, 201 # 201 mean resource created

@app.route('/addreport', methods = ['POST'])
@auth.login_required
def new_report():
       """Agrega un reporte para el usuario logeado"""
       year = request.json.get('year')
       month = request.json.get('month')
       day = request.json.get('day')
       avivamientos = request.json.get('avivamientos', 0)
       hogares = request.json.get('hogares', 0)
       estudios_establecidos = request.json.get('estudios_establecidos', 0)
       estudios_realizados = request.json.get('estudios_realizados', 0)
       estudios_asistidos = request.json.get('estudios_asistidos', 0)
       biblias = request.json.get('biblias', 0)
       mensajeros = request.json.get('mensajeros', 0)
       porciones = request.json.get('porciones', 0)
       visitas = request.json.get('visitas', 0)
       ayunos = request.json.get('ayunos', 0)
       horas_ayunos = request.json.get('horas_ayunos', 0)
       enfermos = request.json.get('enfermos', 0)
       sanidades = request.json.get('sanidades', 0)
       mensajes = request.json.get('mensajes', 0)
       cultos = request.json.get('cultos', 0)
       devocionales = request.json.get('devocionales', 0)
       horas_trabajo = request.json.get('horas_trabajo', 0)
       otros = request.json.get('otros', '')

       date = datetime.date.today()
       report = Report(
              fecha = date,
              year = year,
              month = month,
              day = day,
              avivamientos = avivamientos,
              hogares = hogares,
              estudios_establecidos= estudios_establecidos,
              estudios_realizados =estudios_realizados,
              estudios_asistidos = estudios_asistidos,
              biblias = biblias,
              mensajeros = mensajeros,
              porciones = porciones,
              visitas = visitas,
              ayunos = ayunos,
              horas_ayunos =horas_ayunos,
              enfermos = enfermos,
              sanidades = sanidades,
              mensajes = mensajes,
              cultos = cultos,
              devocionales = devocionales,
              horas_trabajo = horas_trabajo,
              otros = otros,
              user = g.user)
       session.add(report)
       session.commit()
       return jsonify({ 'report': report.id })#, 201 # 201 mean resource created

@app.route('/<int:report_id>/edit', methods = ['POST'])
@auth.login_required
def edit_report(report_id):
       try:
              report = session.query(Report).filter_by(id=report_id).one()
       except:
              return jsonify({'message':'report not exists'})#, 200

       if report.user_id != g.user.id:
              return jsonify({'message':'The report belong to another user'})#, 200
       avivamientos = request.json.get('avivamientos')
       if avivamientos is not None:
              report.avivamientos = avivamientos
       hogares = request.json.get('hogares')
       if hogares is  not None:
              report.hogares = hogares
       estudios_establecidos = request.json.get('estudios_establecidos')
       if estudios_establecidos is not None:
              report.estudios_establecidos =estudios_establecidos
       estudios_realizados = request.json.get('estudios_realizados')
       if estudios_realizados is not None:
              report.estudios_realizados = estudios_realizados
       estudios_asistidos = request.json.get('estudios_asistidos')
       if estudios_asistidos is not None:
              report.estudios_asistidos = estudios_asistidos
       biblias = request.json.get('biblias')
       if biblias is not None:
              report.biblias = biblias
       mensajeros = request.json.get('mensajeros')
       if mensajeros is not None:
              report.mensajeros = mensajeros
       porciones = request.json.get('porciones')
       if porciones is not None:
              report.porciones = porciones
       visitas = request.json.get('visitas')
       if visitas is not None:
              report.visitas = visitas
       ayunos = request.json.get('ayunos')
       if ayunos is not None:
              report.ayunos = ayunos
       horas_ayunos = request.json.get('horas_ayunos')
       if horas_ayunos is not None:
              report.horas_ayunos = horas_ayunos
       enfermos = request.json.get('enfermos')
       if enfermos is not None:
              report.enfermos = enfermos
       sanidades = request.json.get('sanidades')
       if sanidades is not None:
              report.sanidades = sanidades
       mensajes = request.json.get('mensajes')
       if mensajes is not None:
              report.mensajes = mensajes
       cultos = request.json.get('cultos')
       if cultos is not None:
              report.cultos = cultos
       devocionales = request.json.get('devocionales')
       if devocionales is not None:
              report.devocionales = devocionales
       horas_trabajo = request.json.get('horas_trabajo')
       if horas_trabajo is not None:
              report.horas_trabajo = horas_trabajo
       otros = request.json.get('otros')
       if otros is not None:
              report.otros = otros
       session.add(report)
       session.commit()
       return jsonify({ 'report': report.id })#, 201 # 201 mean resource created

@app.route('/addbiblical', methods = ['POST'])
@auth.login_required
def new_biblical():
       """Agrega un estudio biblico para el usuario logeado"""
       year = request.json.get('year')
       month = request.json.get('month')
       day = request.json.get('day')
       nombre = request.json.get('nombre', '')
       direccion = request.json.get('direccion', '')

       init_fecha = datetime.date.today()
       biblical = Biblical(
              init_fecha = init_fecha,
              year = year,
              month = month,
              day = day,
              nombre = nombre,
              direccion = direccion,
              user = g.user)
       session.add(biblical)
       session.commit()
       return jsonify({ 'biblical': biblical.id })

# JSON api to get the user information base in the id
@app.route('/user/<int:user_id>.json')
@auth.login_required
def getUserJSON(user_id):
       result={'status':'ok'}
       try:
              user = session.query(User).filter_by(id=user_id).one()
              result.update(user.serialize)
       except:
              result['status'] = 'fail'
       return jsonify(User=result)

# JSON api to get the user information base in the email
@app.route('/getuser')
@auth.login_required
def getUserDataJSON():
       result={'status':'ok'}
       email = g.user.email
       try:
              user = session.query(User).filter_by(email = email).first()
              result.update(user.serialize)
       except:
              result['status'] = 'fail'
       return jsonify(result)

# JSON api to get all reports for an user id (/reports?user_id=a)
@app.route('/reports', methods = ['GET'])
@auth.login_required
def getReportsJSON():
       result={'status':'ok'}
       user_id = request.args.get('user_id')
       try:
              user = session.query(User).filter_by(id=user_id).one()
              reports = session.query(Report).filter_by(user_id=user.id).order_by(-Report.id).limit(24)
              report_list = []
              for report in reports:
                     report_list.append(report.serialize)
              temp = {'list':report_list}
              result.update(temp)
       except:
              result['status'] = 'fail'
       return jsonify(Reports=result)

# JSON api to get the report base in the report id (/report?report_id=a)
@app.route('/report', methods = ['GET'])
@auth.login_required
def getReportJSON():
       result={'status':'ok'}
       report_id = request.args.get('report_id')
       try:
              report = session.query(Report).filter_by(id=report_id).one()
              result.update(report.serialize)
       except:
              result['status'] = 'fail'
       return jsonify(Report=result)

# JSON api to get all biblical for an user id (/biblicals?user_id=a)
@app.route('/biblicals', methods = ['GET'])
@auth.login_required
def getBiblicalJSON():
       result={'status':'ok'}
       user_id = request.args.get('user_id')
       try:
              user = session.query(User).filter_by(id=user_id).one()
              biblicals = session.query(Biblical).filter_by(user_id=user.id).order_by(-Biblical.id).limit(24)
              biblical_list = []
              for biblic in biblicals:
                     biblical_list.append(biblic.serialize)
              temp = {'list':biblical_list}
              result.update(temp)
       except:
              result['status'] = 'fail'
       return jsonify(Biblicals=result)

if __name__ == '__main__':
    app.secret_key = '88040422507vryyo'
    app.debug = True
    app.run(host='0.0.0.0', port=8000) # app.run(threaded=True) tampoco sirvio para arreglar broken Pipe