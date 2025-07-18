from flask import Flask
from flask_mongoengine import MongoEngine
from routes import register_routes
from flask_login import LoginManager
from flask import  render_template, url_for

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': 'Google_Scholar',
    'host': 'localhost',
    'port': 27017
}

db = MongoEngine(app)
app.config['SECRET_KEY'] = 'More16'

# Initialize the Flask-Login extension
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.objects(id=user_id).first()

register_routes(app)

if __name__ == '__main__':
    app.run(debug=True)