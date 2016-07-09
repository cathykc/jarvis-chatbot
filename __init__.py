from database import db
from flask import Flask
import uuid

def create_app():
	app = Flask(__name__)
	app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
	db.init_app(app)
	app.secret_key = str(uuid.uuid4())
	return app