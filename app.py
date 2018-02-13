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

@app.route('/user', methods = ['POST'])
def new_user():
       user_name = request.json.get('username')
       password = request.json.get('password')
       if username is None or password is None:
              print "missing arguments"
              abort(400)
       if session.query(User).filter_by(email = username).first() is not None:
              print "existing user"
              user = session.query(User).filter_by(email=username).first()
              return jsonify({'message':'user already exists'}), 200

       user = User(email = username)
       user.hash_password(password)
       session.add(user)
       session.commit()
       return jsonify({ 'username': user.username }), 201

# JSON api to get the user information base in the id
@app.route('/user/<int:user_id>.json')
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