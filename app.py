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

# For auth token and password
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///report.db')
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
       else: # No es un token sino usuario(siempre el email) y password
              user = session.query(User).filter_by(email = username_or_token).first()
              if not user or not user.verify_password(password):
                     return False
       g.user = user
       return True

@app.route('/token')
@auth.login_required
def get_auth_token():
       """ Genera un token para el usuario dado en los parametros"""
       token = g.user.generate_auth_token()
       return jsonify({'token': token.decode('ascii')})

@app.route('/user', methods = ['POST'])
def new_user():
       """ Crea un usuario"""
       nombre = request.json.get('nombre')
       email = request.json.get('email') # username es el email
       grado = request.json.get('grado')
       ministerio = request.json.get('ministerio')
       responsabilidad = request.json.get('responsabilidad')
       lugar = request.json.get('lugar')
       pastor = request.json.get('pastor')
       password = request.json.get('password')

       if email is None or password is None or lugar is None or nombre is None:
              print "missing arguments"
              abort(400)
       if session.query(User).filter_by(email = email).first() is not None:
              print "existing user"
              user = session.query(User).filter_by(email=email).first()
              return jsonify({'message':'user already exists'}), 200

       user = User(nombre = nombre, email = email, grado = grado,
              ministerio = ministerio, responsabilidad =responsabilidad,
              lugar = lugar, pastor = pastor)
       user.hash_password(password)
       session.add(user)
       session.commit()
       return jsonify({ 'email': user.email }), 201 # 201 mean resource created

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

# JSON api to get all reports for an user id (/reports?user_id=a)
@app.route('/reports', methods = ['GET'])
@auth.login_required
def getReportsJSON():
       result={'status':'ok'}
       user_id = request.args.get('user_id')
       try:
              user = session.query(User).filter_by(id=user_id).one()
              reports = session.query(Report).filter_by(user_id=user.id).all()
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

if __name__ == '__main__':
    app.secret_key = '88040422507vryyo'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)