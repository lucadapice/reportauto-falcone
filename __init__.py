from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
CORS(app, origins=[
    "https://reportauto.it",
    "https://www.reportauto.it",
    "https://reportscar.it",
    "https://www.reportscar.it"
])

# Configura il database (SQLite in questo esempio)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disabilita avvisi non necessari
db = SQLAlchemy(app)

from . import routes, models  # Importa anche il file models.py che creeremo