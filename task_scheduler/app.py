from flask import Flask
from flask_login import LoginManager
from models import db, User
from routes import main, auth

app = Flask(__name__)
app.config['SECRET_KEY'] = 'taskassigner-secret-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

