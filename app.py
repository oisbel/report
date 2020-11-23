# coding: utf-8

import datetime
from datetime import timedelta

from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
from flask import abort, g

# For database
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from database import Base, Member, Report, Biblical, Church, Statistic

# For anti-forgery
from flask import session as login_session
import random
import string

import constants

# for fivicon.ico
import os
from flask import send_from_directory

# to fix IO Error Broken Pipe
#from signal import signal, SIGPIPE, SIG_DFL
#signal(SIGPIPE,SIG_DFL) # no funciono porque en ves de darme el error apaga el servidor, al menos el local

# For auth token and password
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

APPLICATION_NAME = "Reportes WebSite"

app = Flask(__name__)

app.secret_key = '88040422507vryyo'

# Connect to Database and create database session
engine = create_engine('sqlite:///report.db')
# engine = create_engine('postgresql://report:vryyo@localhost/report')
Base.metadata.bind = engine
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

@app.errorhandler(404)
def page_not_found(e):
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       return render_template('404.html', data=data), 404

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def showMain():
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       session = Session()
       nChurchs = session.query(Church).count()
       nUsers = session.query(Member).filter_by(admin=False, profile_complete=True).count()
       nReports = session.query(Report).count()
       nBiblicals = session.query(Biblical).count()       
       data = data = commonData()
       data.churchs = nChurchs
       data.users = nUsers
       data.biblicals = nBiblicals
       data.reports = nReports

       # actualizar los datos del gráfico de reportes
       # poner como ultimo mes: el actual
       actualMonth = datetime.date.today().month
       index = actualMonth
       if actualMonth == 12:
              index = 0
       months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dec"]
       data.months = monthsOrder(months, 12, index)
       monthsValues = [0,0,0,0,0,0,0,0,0,0,0,0]
       statistics = session.query(Statistic).all()
       for statistic in statistics:
              monthsValues[statistic.month-1] = statistic.reports_count
       data.monthsValues = monthsOrder(monthsValues, 12, index)
       session.close()
       return render_template(
              'index.html', data = data)

# aux methods

def commonData():
       """ Devuelve un objeto con los datos comunes que muestran sidebar.html y topbar.html"""
       try:
              data = type ('Data', (object,),{})
              data.user_id = login_session['user_id']
              data.username = login_session['username']
              data.super_admin = login_session['super_admin']
              data.church_id = login_session['church_id']
              return data
       except :
              return redirect(url_for('showLogin'))

def monthsOrder(listMonths, nList, index):
       """Crea la lista de meses poniendo como primer elemento index(utilizando un arrar circular)"""
       result = []
       i = index
       while i < nList + index:
              result.append(listMonths[i % nList])
              i = i + 1
       return result

# end aux methods

@app.route('/login/')
def showLogin():
       # Anti-forgery state token and store in the sesion for later validation
       state = ''.join(random.choice(string.ascii_uppercase + string.digits) 
              for x in range(32))
       login_session['state'] = state
       return render_template(
              'login.html', STATE=state)

@app.route('/connect', methods=['POST'])
def connnect():
       login_session.permanent = True
       app.permanent_session_lifetime = timedelta(minutes=15)
       login_session.pop('username', None)
       try:
              state = request.form['state']
              if state != login_session['state']:
                     return redirect(url_for('showLogin'))
       except :
              flash("Session terminada")
              return redirect(url_for('showLogin'))
       email = request.form['email']
       password = request.form['password']
       session = Session()
       try:
              user = session.query(Member).filter_by(email = email).one()
              if not user or not user.verify_password(password):
                     flash("Credenciales incorrectas")
              elif not user.admin:
                     flash("Usuario no autorizado para entrar al sitio de administracion")
              else:
                     login_session['user_id'] = user.id
                     login_session['username'] = user.nombre
                     login_session['super_admin'] = user.super_admin
                     login_session['church_id'] = user.church_id
                     session.close()
                     return redirect(url_for('showMain'))
       except :
              flash("Entre los datos de usuario")
       session.close()
       return redirect(url_for('showLogin'))

@app.route('/disconnect/')
def disconnect():
       login_session.pop('username', None)
       flash("Se ha cerrado la session satisfactoriamente")
       return redirect(url_for('showLogin'))

@app.route('/changePassword/', methods = ['POST'])
def changePassword():
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       session = Session()
       try:
              user = session.query(Member).filter_by(id=login_session['user_id']).one()
       except :
              flash("No se pudieron verificar los datos de usuario")
              session.close()
              return redirect(url_for('showMain'))
       oldPass = request.form['oldPass']
       if not user.verify_password(oldPass):
              flash(u"Contraseña incorrecta")
              session.close()
              return redirect(url_for('showMain'))              
       newPass = request.form['newPass']
       user.hash_password(newPass)
       session.add(user)
       session.commit()
       flash(u"Se ha cambiado la contraseña satisfactoriamente")
       return redirect(url_for('showMain'))

@app.route('/churchs/')
def showChurchs():
       """Muestra la pagina de la lista de iglesias"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()
       churchs = session.query(Church).all()
       session.close()
       return render_template(
              'churchs.html', churchs = churchs, data = data)

@app.route('/churchs/<int:church_id>/members')
def showMembers(church_id):
       """Muestra la pagina de la lista de usuarios de la iglesia correspondiente"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       data.miembros = 0
       data.misioneros = 0
       data.oficiales = 0
       session = Session()
       try:
              church = session.query(Church).filter_by(id=church_id).one()
              members = session.query(Member).filter_by(church_id=church_id, admin=False).all()
       except :
              flash("Error al intentar mostrar los datos de la iglesia seleccionada")
              session.close()
              return redirect(url_for('showChurchs'))
       for member in members:
              if member.grado in constants.grados[0:3]:
                     data.miembros = data.miembros + 1
              if member.grado in constants.grados[3:9]:
                     data.misioneros = data.misioneros + 1
              if member.grado in constants.grados[9:]:
                     data.oficiales = data.oficiales + 1
       session.close()
       return render_template(
            'members.html', members=members, church=church, data = data)

@app.route('/churchs/<int:user_id>/reports')
def showReports(user_id):
       """Muestra la pagina de la lista de reporte del usuario correspondiente"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()
       try:
              miembro = session.query(Member).filter_by(id=user_id).one()
              reports = session.query(Report).filter_by(user_id=user_id).all()
              church = session.query(Church).filter_by(id=miembro.church_id).one()
       except :
              session.close()
              flash("Error al intentar mostrar los datos de la iglesia seleccionada")
              return redirect(url_for('showAllMembers'))
       session.close()
       return render_template(
            'reportes.html', reports=reports, miembro=miembro, church = church, data = data)

@app.route('/churchs/<int:user_id>/reports/<int:report_id>')
def showReport(user_id, report_id):
       """Muestra la pagina del reporte correspondiente"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()
       miembro = session.query(Member).filter_by(id=user_id).one()
       try:
              report = session.query(Report).filter_by(id=report_id, user_id=user_id).one()
              session.close()
       except:
              flash("{} El reporte para el usuario especificado no existe".format(report_id))
              session.close()
              return showReports(user_id)
       return render_template(
              'reporte.html', report=report, miembro=miembro, data=data)

@app.route('/all-members/')
def showAllMembers():
       """Muestra la pagina de la lista de toda la tabla Member(para superUsuario, para un admin solo los de su iglesia)"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       # Si es solo un usuario admin, mostrar solo los miembros de su localidad.
       if not data.super_admin:
              return redirect(url_for('showMembers',church_id = data.church_id))
       
       session = Session()
       members = session.query(Member).filter_by(admin=False).all()
       churchs = session.query(Church).all()
       diccChurchs = {}
       for church in churchs:
              diccChurchs[church.id] = church.nombre
       session.close()
       return render_template(
              'all-members.html', members = members, data = data, churchs = diccChurchs)

@app.route('/all-reports/<int:church_id>')
def showAllReports(church_id):
       """Muestra la pagina de la lista de reportes de la iglesia especificada"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()
       try:
              church = session.query(Church).filter_by(id=church_id).one()
       except :
              flash("La iglesia especificada ({}) no existe".format(church_id))
              session.close()
              return redirect(url_for('showAllMembers'))
       reports = []
       users = session.query(Member).filter_by(church_id=church_id).all()
       diccUsers = {}
       for user in users:
              diccUsers[user.id] = user.nombre
              reports.extend(session.query(Report).filter_by(user_id=user.id).all())
       session.close()
       return render_template(
              'all-reports.html', reports = reports, data = data, users = diccUsers, church_nombre=church.nombre)

@app.route('/addUser', methods = ['GET','POST'])
def addUser():
       """Muestra los formularios para agregar usuarios, agrega usuarios regulares con TODA la informacion"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()
       if request.method == 'POST':
              if request.form:
                     # Verificar si es el super administrador para seleccionar la iglesia
                     if data.super_admin:
                            church_id = request.form['churchMember']
                     else:
                            church_id = data.church_id
                     nombre = request.form['nombre']
                     phone = request.form['phone']
                     direccion = request.form['direccion']
                     birthday = datetime.datetime.strptime(request.form['birthday'], '%Y-%m-%d')
                     year = 1900
                     month = 1
                     day = 1
                     if birthday is not None:
                            year = birthday.year
                            month = birthday.month
                            day = birthday.day
                     nombre_conyuge = request.form['nombre_conyuge']
                     try:
                            fecha_casamiento = datetime.datetime.strptime(request.form['fecha_casamiento'], '%Y-%m-%d')
                     except:
                            fecha_casamiento = None
                     grado = request.form['grado']
                     ministerio = request.form['ministerio']
                     responsabilidad = request.form['responsabilidad']
                     email = request.form['email']
                     password = request.form['password']    
                     try:                            
                            church = session.query(Church).filter_by(id=church_id).one()
                     except :
                            flash("Error: La iglesia asignada a este usuario no existe")
                            session.close()
                            return redirect(url_for('addUser'))                     
              if nombre == '' or email == '' or direccion == '':
                     flash("Nombre, correo, direccion son campos abligatorios")
                     session.close()
                     return redirect(url_for('addUser'))
              if session.query(Member).filter_by(email = email).first() is not None:
                     # existin user
                     session.close()
                     flash("Ya existe una cuenta de usuario vinculada al correo ({})".format(email))
                     return redirect(url_for('addUser'))
              
              user = Member(nombre = nombre, email = email, phone = phone, grado = grado, 
                     year = year, month = month, day = day, direccion = direccion,
                     nombre_conyuge = nombre_conyuge, fecha_casamiento = fecha_casamiento,
                     ministerio = ministerio, responsabilidad =responsabilidad, profile_complete = True, church =church)
              user.hash_password(password)
              # aunmentar el numero de feligresia de la iglesia
              church.feligresia = church.feligresia + 1
              session.add(user)
              session.add(church)
              session.commit()
              flash(u"El usuario {} se ha agregado correctamente.".format(user.nombre))
              return redirect(url_for('showMembers',church_id =data.church_id))
       else:
              if data.super_admin:
                     churchs = session.query(Church).all()
                     session.close()
                     return render_template('addUser.html', data=data, churchs=churchs, grados=constants.grados)
              else:
                     try:
                            church = session.query(Church).filter_by(id=data.church_id).one()
                            church_name = church.nombre
                     except :
                             church_name = "None"
                     session.close()
                     return render_template('addUser.html', data=data, church_name=church_name, grados=constants.grados)


@app.route('/newUser', methods = ['POST'])
def newUser():
       '''Agrega un usuario nuevo, solo nombre, email y pass. Con la idea de darles acceso a la app y puedan terminar de crear su cuenta'''
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()

       nombre = request.form['nombre']
       email = request.form['email']
       password = request.form['password']
       if nombre == '' or email == '' or password == '':
              flash("Se recibieron valores nulos")
              session.close()
              return redirect(url_for('addUser'))
       if session.query(Member).filter_by(email = email).first() is not None:
              flash("Ya existe una cuenta de usuario vinculada al correo ({})".format(email))
              session.close()
              return redirect(url_for('addUser'))
       if data.super_admin:
              church_id = request.form['churchUser']
       else:
              church_id = data.church_id
       try:
              church = session.query(Church).filter_by(id=church_id).one()
       except :
              session.close()
              flash("Error: La iglesia asignada a este usuario no existe")
              return redirect(url_for('addUser'))
       user = Member(nombre = nombre, email = email, church= church)
       user.hash_password(password)
       session.add(user)
       session.commit()
       flash(u"El usuario {} se ha agregado correctamente.".format(user.nombre))
       return redirect(url_for('addUser'))

@app.route('/addAdmins', methods = ['GET','POST'])
def addAdmins():
       """Muestra el formulario para agregar administradores nuevos, y ademas muestra la lista de admins"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()
       if request.method == 'POST':
              if request.form:
                     nombre = request.form['nombre']
                     email = request.form['email']
                     password = request.form['password']
                     church_id = request.form['church']
                     try:
                            church = session.query(Church).filter_by(id=church_id).one()
                     except :
                            session.close()
                            flash("La iglesia especificada no existe")
                            return redirect(url_for('addAdmins')) 
              if nombre is not None and email is not None and password is not None and church is not None:
                     user = Member(nombre = nombre, email = email, church= church, admin=True)
                     user.hash_password(password)
                     session.add(user)
                     session.commit()
                     flash(u"El usuario {} para la congregación de {} se ha agregado correctamente.".format(user.nombre, church.nombre))
              else:
                     session.close()
              return redirect(url_for('addAdmins'))   
       else:
              churchs = session.query(Church).all()
              users = session.query(Member).filter_by(admin=True).all()
              diccChurchs = {}
              for church in churchs:
                     diccChurchs[church.id] = church.nombre
              session.close()
              return render_template('addAdmins.html', data=data, churchs=churchs, users=users, diccChurchs=diccChurchs)

@app.route('/deleteadmin/<int:user_id>')
def delete_admin(user_id):
       """No muestra ninguna pagina,solo ejecuta la eliminacion del usuario administrador correspondiente"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))      
       session = Session()
       try:
              user = session.query(Member).filter_by(id=user_id).one()
              if user.super_admin:
                     session.close()
                     flash("No se puede eliminar al super usuario")
                     return redirect(url_for('addAdmins'))
              session.delete(user)
              session.commit()
              flash(u"El usuario administrador {} se ha eliminado satisfactoriamente.".format(user.nombre))  
       except:
              session.close()
              flash("Error al eliminar el usuario")
       return redirect(url_for('addAdmins'))

@app.route('/addChurch', methods = ['GET','POST'])
def addChurch():
       """Muestra el formulario y agrega una iglesia nueva"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       if request.method == 'POST':
              if request.form:
                     nombre = request.form['nombre']
                     pais = request.form['pais']
                     direccion = request.form['direccion']
                     pastor = request.form['pastor']
              if nombre == '' or direccion == '':
                     flash("Nombre, pais son campos abligatorios")
                     return redirect(url_for('addChurch'))
              church = Church(
              nombre = nombre,
              pais = pais,
              direccion = direccion,
              pastor = pastor)
              session = Session()
              session.add(church)
              session.commit()
              flash(u"La iglesia {} se ha agregado correctamente.".format(church.nombre))
              return redirect(url_for('showChurchs'))
       else:
              return render_template('addChurch.html', data=data)

@app.route('/adminChurchs')
def adminChurchs():
       """Muestra la lista de iglesias con el boton de editar y eliminar"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()
       churchs = session.query(Church).all()
       session.close()
       return render_template('adminChurchs.html',churchs=churchs, data=data)

@app.route('/deletechurch/<int:church_id>')
def delete_church(church_id):
       """No muestra ninguna pagina,solo ejecuta la eliminacion del la iglesia correspondiente"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))      
       session = Session()
       try:
              church = session.query(Church).filter_by(id=church_id).one()
              members = session.query(Member).filter_by(church_id=church_id).first()
              if members is None:
                     session.delete(church)
                     session.commit()
                     flash(u"La iglesia {} se ha eliminado satisfactoriamente.".format(church.nombre))
              else:
                   flash(u"La iglesia {} no se puede eliminar porque tiene miembros asignados a ella.".format(church.nombre))
                   session.close()  
       except:
              session.close()
              flash("No se puede eliminar la iglesia con ese ID.")
       return redirect(url_for('adminChurchs'))

@app.route('/editchurch/<int:church_id>',  methods = ['GET','POST'])
def edit_church(church_id):
       """Muestra la pagina de edicion de iglesias y ejecuta la consulta para cambiarla"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()
       try:
              church = session.query(Church).filter_by(id=church_id).one()
       except :
              session.close()
              flash("La iglesia especificada no existe")
              return redirect(url_for('adminChurchs'))
       if request.method == 'POST':
              if request.form:
                     nombre = request.form['nombre']
                     direccion = request.form['direccion']
                     pastor = request.form['pastor']
              if nombre == '' or direccion == '' or pastor == '':
                     flash("Nombre, direccion y pastor son campos abligatorios")
                     session.close()
                     return redirect(url_for('edit_church', church_id=church_id))
              church.nombre = nombre
              church.direccion = direccion
              church.pastor = pastor
              session.add(church)
              session.commit()
              flash("Datos de Iglesia cambiados exitosamente")
              return redirect(url_for('adminChurchs'))
       else:
              session.close()
              return render_template('editChurch.html', data=data, church=church)
       
@app.route('/activate-deactivate/<int:user_id>/<int:active_value>')
def activateDeactivate(user_id, active_value):
       """Muestra la pagina de la lista de toda la tabla Member con el propósito de activar o desactivar usuarios"""
       if 'username' not in login_session:
              return redirect(url_for('showLogin'))
       data = commonData()
       session = Session()
       if data.super_admin:
              members = session.query(Member).filter_by(admin=False).all()
       else:
              members = session.query(Member).filter_by(church_id=data.church_id, admin=False).all()
       churchs = session.query(Church).all()
       diccChurchs = {}
       for church in churchs:
              diccChurchs[church.id] = church.nombre
       if user_id == 0 and active_value == 2:
              # Es un get request de mostrar la pagina con los usuarios para cambiar el estado activo
              session.close()
              return render_template(
                     'activate-deactivate.html', members = members, data = data, churchs = diccChurchs)
       else:
              # es como un post request pero es un link para cambiar el estado activo de un usuario
              try:
                     user = session.query(Member).filter_by(id=user_id).one()
                     if active_value == 0:
                            user.active = False
                     else:
                            user.active = True
                     session.add(user)
                     session.commit()
                     flash("Estado de usuario cambiado satisfactoriamente")
                     return render_template(
                            'activate-deactivate.html', members = members, data = data, churchs = diccChurchs)
              except :
                     flash("El usuario especificado no existe")
                     session.close()
                     return render_template(
                            'activate-deactivate.html', members = members, data = data, churchs = diccChurchs)  

@auth.verify_password
def verify_password(username_or_token, password):
       """ Usado por HTTPBasicAuth para verificar
        que sea un usuario el que accede a las funciones con el decorador @auth.verify_password
        Se ha agregado un token para no tener que transmitir por la web el usurio y password """
       # Try to see if it's a token first
       session = Session()
       user_id = Member.verify_auth_token(username_or_token)
       if user_id:
              user = session.query(Member).filter_by(id = user_id).one()
              session.close()
       else: # No es un token sino credenciales de usuario(siempre el email y password)
              try:
                     user = session.query(Member).filter_by(email = username_or_token).one()
                     session.close()
                     if not user or not user.verify_password(password):
                            session.close()
                            return False
              except: #Era un token invalido
                     return False

       if not user.active:
              return False
       g.user = user
       return True

@app.route('/token')
@auth.login_required
def get_auth_token():
       """ Genera un token para el usuario dado en los parametros"""
       token = g.user.generate_auth_token()
       return jsonify({'token': token.decode('ascii')})

#
# A partir de aqui estan las API para los requests Android and IOS
#

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
              user = session.query(Member).filter_by(id=user_id).one()
              report = session.query(Report).filter_by(user_id=user.id).order_by(-Report.id).first()
              if report is not None:
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

@app.route('/edituser/<int:user_id>', methods = ['POST'])
@auth.login_required
def edit_user(user_id):
       session = Session()
       try:
              user = session.query(Member).filter_by(id=user_id).one()
       except:
              session.close()
              return jsonify({'message':'user not exists'})#, 200

       if user.id != g.user.id:
              session.close()
              return jsonify({'message':'different user'})#, 200
       nombre = request.json.get('nombre')
       if nombre is not None:
              user.nombre = nombre
       phone = request.json.get('phone')
       if phone is not None:
              user.phone = phone
       year = request.json.get('year')
       if year is not None:
              user.year = year
       month = request.json.get('month')
       if month is not None:
              user.month = month
       day = request.json.get('day')
       if day is not None:
              user.day = day
       direccion = request.json.get('direccion')
       if direccion is not None:
              user.direccion = direccion
       nombre_conyuge = request.json.get('nombre_conyuge')
       if nombre_conyuge is not None:
              user.nombre_conyuge = nombre_conyuge
       fecha_casamiento = request.json.get('fecha_casamiento')
       if fecha_casamiento is not None:
              user.fecha_casamiento = fecha_casamiento
       grado = request.json.get('grado')
       if grado is not None:
              user.grado = grado
       ministerio = request.json.get('ministerio')
       if ministerio is not None:
              user.ministerio = ministerio
       responsabilidad = request.json.get('responsabilidad')
       if responsabilidad is not None:
              user.responsabilidad = responsabilidad
       password = request.json.get('password')
       if password is not None:
              user.hash_password(password)
       user.profile_complete = True
       
       session.add(user)
       session.commit()
       return jsonify({ 'user': user.id })#, 201 # 201 mean resource created

@app.route('/activeuser/<int:user_id>', methods = ['GET'])
def ItIsActiveUser(user_id):
       """ Devuelve true si el usuario esta activo"""
       session = Session()
       result={'active':'true'}
       try:
              user = session.query(Member).filter_by(id=user_id).one()
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
              user = session.query(Member).filter_by(id=user_id).one()
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
       # actualizar la tabla de Statistics con la cantidad de reportes de ese mes
       statistic = session.query(Statistic).filter_by(month=month).first()
       if statistic is None:
              statistic = Statistic(month = month, reports_count =1)
       else:
              statistic.reports_count = statistic.reports_count + 1
       session.add(statistic)
       
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
              user = session.query(Member).filter_by(id=user_id).one()
              result.update(user.serialize)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(Member=result)

# JSON api to get the user information base in the email
@app.route('/getuser')
@auth.login_required
def getUserDataJSON():
       session = Session()
       result={'status':'ok'}
       email = g.user.email
       try:
              user = session.query(Member).filter_by(email = email).one()
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
              users = session.query(Member).all()
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
              user = session.query(Member).filter_by(id=user_id).one()
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
              user = session.query(Member).filter_by(id=user_id).one()
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

# This session is meant to be temporary for ios comunication, since I dont know how to manage auth reguest in swift
def VerifyCredentials(email, password):
       session = Session()
       try:
              user = session.query(Member).filter_by(email = email).one()
              session.close()
              if not user or not user.verify_password(password):
                     session.close()
                     return False
       except:
              return False

       if not user.active:
              return False
       g.user = user
       return True

# JSON api to get the user information base in the email for IOS
@app.route('/getuser-ios/<string:email>/<string:password>')
def getUserIOS(email,password):
       session = Session()
       result={'status':'ok'}
       try:
              user = session.query(Member).filter_by(email = email).one()
              if not user.verify_password(password):
                     result['status'] = 'fail'
                     session.close()
                     return jsonify(result)
              result.update(user.serialize)
       except:
              result['status'] = 'fail'
       session.close()
       return jsonify(result)


@app.route('/edituser-ios/<int:user_id>', methods = ['POST'])
def edit_userIOS(user_id):
       session = Session()
       try:
              user = session.query(Member).filter_by(id=user_id).one()
       except:
              session.close()
              return jsonify({'message':'user not exists'})#, 200

       oldpassword = request.json.get('oldpassword')
       if oldpassword is None:
              session.close()
              return jsonify({'message':'empty password'})
       if not user.verify_password(oldpassword):
              session.close()
              return jsonify({'message':'invalid password'})
       nombre = request.json.get('nombre')
       if nombre is not None:
              user.nombre = nombre
       phone = request.json.get('phone')
       if phone is not None:
              user.phone = phone
       year = request.json.get('year')
       if year is not None:
              user.year = year
       month = request.json.get('month')
       if month is not None:
              user.month = month
       day = request.json.get('day')
       if day is not None:
              user.day = day
       direccion = request.json.get('direccion')
       if direccion is not None:
              user.direccion = direccion
       nombre_conyuge = request.json.get('nombre_conyuge')
       if nombre_conyuge is not None:
              user.nombre_conyuge = nombre_conyuge
       fecha_casamiento = request.json.get('fecha_casamiento')
       if fecha_casamiento is not None:
              user.fecha_casamiento = fecha_casamiento
       grado = request.json.get('grado')
       if grado is not None:
              user.grado = grado
       ministerio = request.json.get('ministerio')
       if ministerio is not None:
              user.ministerio = ministerio
       responsabilidad = request.json.get('responsabilidad')
       if responsabilidad is not None:
              user.responsabilidad = responsabilidad
       password = request.json.get('password')
       if password is not None:
              user.hash_password(password)
       user.profile_complete = True
       
       session.add(user)
       session.commit()
       return jsonify({ 'user': user.id })#, 201 # 201 mean resource created

# JSON api to see if it is time to create a new report or just edit the last one
@app.route('/ask-ios/<string:email>/<string:password>', methods = ['GET'])
def ItIsTimeToNewReportIOS(email,password):
       """ Devuelve yes si es tiempo del nuevo reporte,
       o sea el ultimo reporte del usuario es de un mes distinto
       del actual y ya ha pasado el dia 7"""

       itIsTime = True

       actual_month = datetime.date.today().month
       actual_day = datetime.date.today().day

       result={'status':'ok'}

       if not VerifyCredentials(email, password):
              result = {'status':'fail-contraseña incorrecta'}
              return jsonify(result)
       
       session = Session()
       user_id = g.user.id
       try:
              user = session.query(Member).filter_by(id=user_id).one()
              report = session.query(Report).filter_by(user_id=user.id).order_by(-Report.id).first()
              if report is not None:
                     if(report.month == actual_month):
                            itIsTime = False
                     elif(actual_day < 8):
                            if((report.month + 1 == actual_month) or (report.month == 12 and actual_month == 1) ):
                                   itIsTime = False
       except:
              result['status'] = 'fail'
       if not itIsTime:
              result.update({'report':report.serialize})
       session.close()
       return jsonify(result)

@app.route('/addreport-ios', methods = ['POST'])
def new_reportIOS():
       """Agrega un reporte para el usuario logeado"""

       email = request.json.get('email')
       password = request.json.get('password')

       if not VerifyCredentials(email, password):
              result = {'message':'Credenciales Incorrectas'}
              return jsonify(result)
       
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
       # actualizar la tabla de Statistics con la cantidad de reportes de ese mes
       statistic = session.query(Statistic).filter_by(month=month).first()
       if statistic is None:
              statistic = Statistic(month = month, reports_count =1)
       else:
              statistic.reports_count = statistic.reports_count + 1
       session.add(statistic)
       
       session.commit()
       return jsonify({ 'report': report.id })#, 201 # 201 mean resource created

@app.route('/editreport-ios/<int:report_id>', methods = ['POST'])
def edit_reportIOS(report_id):
       
       email = request.json.get('email')
       password = request.json.get('password')

       if not VerifyCredentials(email, password):
              result = {'message':'Credenciales Incorrectas'}
              return jsonify(result)
       
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

@app.route('/addbiblical-ios', methods = ['POST'])
def new_biblicalIOS():
       """Agrega un estudio biblico para el usuario logeado"""
       
       email = request.json.get('email')
       password = request.json.get('password')

       if not VerifyCredentials(email, password):
              result = {'message':'Credenciales Incorrectas'}
              return jsonify(result)
       
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

@app.route('/deletebiblical-ios/<int:biblical_id>', methods = ['POST'])
def delete_biblicalIOS(biblical_id):
       
       email = request.json.get('email')
       password = request.json.get('password')

       if not VerifyCredentials(email, password):
              result = {'message':'Credenciales Incorrectas'}
              return jsonify(result)

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

# JSON api to get all reports for a user
@app.route('/reports-ios/<string:email>/<string:password>', methods = ['GET'])
def getReportsIOS(email, password):
       if not VerifyCredentials(email, password):
              result = {'message':'Credenciales Incorrectas'}
              return jsonify(result)
       session = Session()
       result = []
       user_id = g.user.id
       try:
              user = session.query(Member).filter_by(id=user_id).one()
              reports = session.query(Report).filter_by(user_id=user.id).order_by(-Report.id).limit(24)
              for report in reports:
                     result.append(report.serialize)
       except:
              result = {'message':'No se pudo obtener los datos de usuario'}
       session.close()
       return jsonify({'reports':result})

# JSON api to get all biblical for a user
@app.route('/biblicals-ios/<string:email>/<string:password>', methods = ['GET'])
def getBiblicalIOS(email, password):
       if not VerifyCredentials(email, password):
              result = {'message':'Credenciales Incorrectas'}
              return jsonify(result)
       session = Session()
       result = []
       user_id = g.user.id
       try:
              user = session.query(Member).filter_by(id=user_id).one()
              biblicals = session.query(Biblical).filter_by(user_id=user.id).order_by(-Biblical.id).limit(24)              
              for biblic in biblicals:
                     result.append(biblic.serialize)
       except:
              result = {'message':'No se pudo obtener los datos de usuario'}
       session.close()
       return jsonify({'biblicals':result})

if __name__ == '__main__':
    app.secret_key = '88040422507vryyo'
    app.debug = True
    app.run(host='0.0.0.0', port=8000) # app.run(threaded=True) tampoco sirvio para arreglar broken Pipe