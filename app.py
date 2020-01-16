import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
from flask import abort, g

# For database
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from database import Base, User, Report, Biblical, Church

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

APPLICATION_NAME = "Reportes WebSite"

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///report.db')
# engine = create_engine('postgresql://report:vryyo@localhost/report')
Base.metadata.bind = engine
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

@app.route('/')
def showMain():
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = type ('Data', (object,),{})
       data.churchs = 20
       data.users = 230
       data.biblicals = 400
       data.reports = 456546
       data.username = login_session['username']
       return render_template(
              'index.html', data = data)

@app.route('/tables/')
def showTables():
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = type ('Data', (object,),{})
       data.username = login_session['username']
       return render_template(
              'tables.html', data = data)

@app.route('/login/')
def showLogin():
       # Anti-forgery state token and store in the sesion for later validation
       state = ''.join(random.choice(string.ascii_uppercase + string.digits) 
              for x in xrange(32))
       login_session['state'] = state
       return render_template(
              'login.html', STATE=state)

@app.route('/connect', methods=['POST'])
def connnect():
       login_session.pop('username', None)
       if request.args.get('state') != login_session['state']:
              return showLogin()
       email = request.form['email']
       password = request.form['password']
       session = Session()
       try:
              user = session.query(User).filter_by(email = email).one()
              if not user or not user.verify_password(password):
                     flash("Credenciales incorrectas")
              elif not user.admin:
                     flash("Usuario no autorizado para entrar al sitio de administracion")
              else:
                     session.close()
                     login_session['username'] = user.nombre
                     return redirect(url_for('showMain'))
       except :
              flash("Entre los datos de usuario")
       session.close()
       return redirect(url_for('showMain'))

@app.route('/disconnect/')
def disconnect():
       login_session.pop('username', None)
       flash("Se ha cerrado la session satisfactoriamente")
       return redirect(url_for('showLogin'))

@app.route('/churchs/')
def showChurchs():
       """Muestra la pagina de la lista de iglesias"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = type ('Data', (object,),{})
       data.username = login_session['username']
       session = Session()
       churchs = session.query(Church).all()
       session.close()
       return render_template(
              'churchs.html', churchs = churchs, data = data)

@app.route('/churchs/<string:church_id>/members')
def showMembers(church_id):
       """Muestra la pagina de la lista de usuarios de la iglesia correspondiente"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = type ('Data', (object,),{})
       data.username = login_session['username']
       session = Session()
       church = session.query(Church).filter_by(id=church_id).one()
       members = session.query(User).filter_by(church_id=church_id).all()
       session.close()
       return render_template(
            'members.html', members=members, church=church, data = data)

@app.route('/churchs/<int:user_id>/reports')
def showReports(user_id):
       """Muestra la pagina de la lista de reporte del usuario correspondiente"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = type ('Data', (object,),{})
       data.username = login_session['username']
       session = Session()
       miembro = session.query(User).filter_by(id=user_id).one()
       reports = session.query(Report).filter_by(user_id=user_id).all()
       church = session.query(Church).filter_by(id=miembro.church_id).one()
       session.close()
       return render_template(
            'reportes.html', reports=reports, miembro=miembro, church = church, data = data)

@app.route('/churchs/<int:user_id>/reports/<int:report_id>')
def showReport(user_id, report_id):
       """Muestra la pagina del reporte correspondiente"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = type ('Data', (object,),{})
       data.username = login_session['username']
       session = Session()
       miembro = session.query(User).filter_by(id=user_id).one()
       try:
              report = session.query(Report).filter_by(id=report_id, user_id=user_id).one()
              session.close()
       except:
              flash("{} El reporte para el usuario especificado no existe".format(report_id))
              session.close()
              return showReports(user_id)
       return render_template(
              'reporte.html', report=report, miembro=miembro, data=data)



@auth.verify_password
def verify_password(username_or_token, password):
       """ Usado por HTTPBasicAuth para verificar
        que sea un usuario el que accede a las funciones con el decorador @auth.verify_password
        Se ha agregado un token para no tener que transmitir por la web el usurio y password """
       # Try to see if it's a token first
       session = Session()
       user_id = User.verify_auth_token(username_or_token)
       if user_id:
              user = session.query(User).filter_by(id = user_id).one()
              session.close()
       else: # No es un token sino credenciales de usuario(siempre el email y password)
              try:
                     user = session.query(User).filter_by(email = username_or_token).one()
                     session.close()
                     if not user or not user.verify_password(password):
                            session.close()
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
       """ Devuelve yes si es tiempo del nuevo reporte,
       o sea el ultimo reporte del usuario es de un mes distinto
       del actual y ya ha pasado el dia 7"""

       session = Session()

       itIsTime = True

       actual_month = datetime.date.today().month
       actual_day = datetime.date.today().day

       result={'status':'ok'}

       user_id = g.user.id
       try:
              user = session.query(User).filter_by(id=user_id).one()
              report = session.query(Report).filter_by(user_id=user.id).order_by(-Report.id).first()
              if(report.month == actual_month):
                     itIsTime = False
              elif(actual_day < 8):
                     if((report.month + 1 == actual_month) or (report.month == 12 and actual_month == 1) ):
                            itIsTime = False
       except:
              result['status'] = 'fail'
       if not itIsTime:
              result = report.serialize
       session.close()
       return jsonify(result)



@app.route('/adduser', methods = ['POST'])
def new_user():
       """ Crea un usuario"""
       session = Session()
       church_id = request.json.get('church_id')
       if church_id is None:
              session.close()
              return jsonify({'message':'church id missing'})
       try:
              church = session.query(Church).filter_by(id=church_id).one()
       except:
              session.close()
              return jsonify({'message':'church not exists'})#, 200
       nombre = request.json.get('nombre')
       email = request.json.get('email') # username es el email
       grado = request.json.get('grado')
       ministerio = request.json.get('ministerio')
       responsabilidad = request.json.get('responsabilidad')
       admin = request.json.get('admin')
       password = request.json.get('password')

       if email is None or password is None or nombre is None:
              # print "missing arguments"
              session.close()
              abort(400)
              return jsonify({'message':'missing arguments'})
       if session.query(User).filter_by(email = email).first() is not None:
              # print "existing user"
              session.close()
              return jsonify({'message':'user already exists'})#, 200

       user = User(nombre = nombre, email = email, grado = grado,
              ministerio = ministerio, responsabilidad =responsabilidad, admin =admin, church =church)
       user.hash_password(password)
       session.add(user)
       session.commit()
       return jsonify({ 'email': user.email , 'id': user.id})#, 201 # 201 mean resource created

@app.route('/edituser/<int:user_id>', methods = ['POST'])
@auth.login_required
def edit_user(user_id):
       session = Session()
       try:
              user = session.query(User).filter_by(id=user_id).one()
       except:
              session.close()
              return jsonify({'message':'user not exists'})#, 200

       if user.id != g.user.id:
              session.close()
              return jsonify({'message':'different user'})#, 200

       grado = request.json.get('grado')
       if grado is not None:
              user.grado = grado
       ministerio = request.json.get('ministerio')
       if ministerio is not None:
              user.ministerio = ministerio
       responsabilidad = request.json.get('responsabilidad')
       if responsabilidad is not None:
              user.responsabilidad = responsabilidad

       session.add(user)
       session.commit()
       return jsonify({ 'user': user.id })#, 201 # 201 mean resource created

@app.route('/activeuser/<int:user_id>', methods = ['GET'])
def ItIsActiveUser(user_id):
       """ Devuelve true si el usuario esta activo"""
       session = Session()
       result={'active':'true'}
       try:
              user = session.query(User).filter_by(id=user_id).one()
       except:
              return jsonify({'message':'user not exists'})#, 200
       if not user.active:
              result['active'] = "False"
       session.close()
       return jsonify(result)

@app.route('/activechange/<int:user_id>', methods = ['POST'])
@auth.login_required
def ChangeActiveStatus(user_id):
       """ Cambia el estado de un usuario(active)"""
       if not g.user.admin:
              return jsonify({'message':'No granted rights to change users status(active)'})
       session = Session()
       try:
              user = session.query(User).filter_by(id=user_id).one()
       except:
              return jsonify({'message':'user not exists'})#, 200
       
       active_value = request.json.get('active_value')
       if active_value is not None:
              user.active = active_value
       session.add(user)
       session.commit()
       return jsonify(user.serialize)



@app.route('/addreport', methods = ['POST'])
@auth.login_required
def new_report():
       """Agrega un reporte para el usuario logeado"""
       session = Session()
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

@app.route('/editreport/<int:report_id>', methods = ['POST'])
@auth.login_required
def edit_report(report_id):
       session = Session()
       try:
              report = session.query(Report).filter_by(id=report_id).one()
       except:
              session.close()
              return jsonify({'message':'report not exists'})#, 200

       if report.user_id != g.user.id:
              session.close()
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
       try:
              session.add(report)
              session.commit()
       except:
              session.close()
              return jsonify({'message':'Error in characters'})
       return jsonify({ 'report': report.id })#, 201 # 201 mean resource created



@app.route('/deletebiblical/<int:biblical_id>', methods = ['POST'])
@auth.login_required
def delete_biblical(biblical_id):
       session = Session()
       try:
              biblical = session.query(Biblical).filter_by(id=biblical_id).one()
       except:
              session.close()
              return jsonify({'message':'biblical not exists'})#, 200
       if(biblical.user_id != g.user.id):
              session.close()
              return jsonify({'message':'You are not authorized to delete this biblical'})#, 200
       session.delete(biblical)
       session.commit()
       return jsonify({'biblical':biblical.id})

@app.route('/addbiblical', methods = ['POST'])
@auth.login_required
def new_biblical():
       """Agrega un estudio biblico para el usuario logeado"""
       session = Session()
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
       session = Session()
       result={'status':'ok'}
       try:
              user = session.query(User).filter_by(id=user_id).one()
              result.update(user.serialize)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(User=result)

# JSON api to get the user information base in the email
@app.route('/getuser')
@auth.login_required
def getUserDataJSON():
       session = Session()
       result={'status':'ok'}
       email = g.user.email
       try:
              user = session.query(User).filter_by(email = email).first()
              result.update(user.serialize)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(result)

# JSON api to get all the users info
@app.route('/getallusers')
@auth.login_required
def getAllUsersJSON():
       """ Devuele la lista de todos los usuarios en formato JSON"""
       if not g.user.admin:
              return jsonify({'message':'No granted rights to get that users info'})
       session = Session()
       result={'status':'ok'}
       try:
              users = session.query(User).all()
              users_list = []
              for user in users:
                     users_list.append(user.serialize)
              temp = {'list':users_list}
              result.update(temp)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(result)

# JSON api to get all reports for an user id (/reports?user_id=a)
@app.route('/reports', methods = ['GET'])
@auth.login_required
def getReportsJSON():
       session = Session()
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
       session.close()
       return jsonify(Reports=result)

# JSON api to get the report base in the report id (/report?report_id=a)
@app.route('/report', methods = ['GET'])
@auth.login_required
def getReportJSON():
       session = Session()
       result={'status':'ok'}
       report_id = request.args.get('report_id')
       try:
              report = session.query(Report).filter_by(id=report_id).one()
              result.update(report.serialize)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(Report=result)

# JSON api to get all biblical for an user id (/biblicals?user_id=a)
@app.route('/biblicals', methods = ['GET'])
@auth.login_required
def getBiblicalJSON():
       session = Session()
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
       session.close()
       return jsonify(Biblicals=result)

# JSON api to get all the biblicals info
@app.route('/getallbiblicals')
@auth.login_required
def getAllBiblicalsJSON():
       """ Devuele la lista de todos los estudios biblicos en formato JSON"""
       if not g.user.admin:
              return jsonify({'message':'No granted rights to get that biblicals info'})
       session = Session()
       result={'status':'ok'}
       try:
              biblicals = session.query(Biblical).all()
              biblical_list = []
              for biblic in biblicals:
                     biblical_list.append(biblic.serialize)
              temp = {'list':biblical_list}
              result.update(temp)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(result)

# JSON api to get churchs info
@app.route('/getchurchs')
def getChurchsJSON():
       """ Devuele la lista de todos las iglesias"""
       session = Session()
       result={'status':'ok'}
       try:
              churchs = session.query(Church).all()
              church_list = []
              for church in churchs:
                     church_list.append(church.serialize)
              temp = {'list':church_list}
              result.update(temp)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(result)


if __name__ == '__main__':
    app.secret_key = '88040422507vryyo'
    app.debug = True
    app.run(host='0.0.0.0', port=8000) # app.run(threaded=True) tampoco sirvio para arreglar broken Pipe