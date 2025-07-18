from flask_mongoengine import MongoEngine
from flask_login import UserMixin
from flask_login import current_user

db = MongoEngine()

class User(db.Document, UserMixin):
    username = db.StringField(required=True, unique=True)
    email = db.EmailField(required=True, unique=True)
    password = db.StringField(required=True)
    profiles = db.ListField(db.ReferenceField('Profile'))

    meta = {
        'collection': 'Users'
    }

    def is_active(self):
        """
        This is required by Flask-Login
        """
        return True

class Profile(db.Document):
    name = db.StringField(required=True)
    query = db.StringField(required=True)
    generated_excel_path = db.StringField()
    owner_id = db.ObjectIdField(required=True)

    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)
        if 'owner_id' not in kwargs:
            self.owner_id = current_user.id

    meta = {
        'collection': 'Profiles'
    }