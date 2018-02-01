from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify

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
       return "SCC Reportes"


if __name__ == '__main__':
    app.secret_key = '88040422507vryyo'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)