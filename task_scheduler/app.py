import os
from flask import Flask
from flask_login import LoginManager
from models import db, User
from routes import main, auth

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SECRET_KEY'] = 'taskassigner-secret-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'tasks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.template_filter('to12hr')
def to12hr_filter(time_str):
    """Converts 24-hour time string like '18:00' to 12-hour format like '6:00 PM'"""
    if not time_str:
        return ''
    try:
        from datetime import datetime as dt
        time_obj = dt.strptime(time_str, '%H:%M')
        return time_obj.strftime('%I:%M %p').lstrip('0')
    except:
        return time_str

app.register_blueprint(main)
app.register_blueprint(auth)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created.")
    app.run(debug=True)