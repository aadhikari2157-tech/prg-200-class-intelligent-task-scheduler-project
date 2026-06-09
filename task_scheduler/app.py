from flask import Flask
from flask_login import LoginManager
from models import db, User
from routes import main, auth

