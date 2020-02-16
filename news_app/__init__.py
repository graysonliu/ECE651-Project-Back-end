from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
import subprocess

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ece651'
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@localhost:3306/ece651"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# crawler
subprocess.run(['python', 'news_app/crawlers/crawlers.py'], timeout=5, stdout=subprocess.DEVNULL,
               stderr=subprocess.DEVNULL)

from news_app.models import *

NewsCategory.query.delete()
id = 1
db.session.add(NewsCategory(id=id, name='University'))
id += 1
with open('./news_app/crawlers/faculties-academics', 'r') as f:
    faculties_academics_sources = eval(f.read())
    for category in faculties_academics_sources.keys():
        db.session.add(NewsCategory(id=id, name=category))
        id += 1

with open('./news_app/crawlers/offices-services', 'r') as f:
    offices_services_sources = eval(f.read())
    for category in offices_services_sources.keys():
        db.session.add(NewsCategory(id=id, name=category))
        id += 1

db.session.commit()

from news_app import routes, errors, commands
