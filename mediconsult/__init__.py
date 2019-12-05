import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
import sqlalchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'REDACTED'


# GCP
CLOUDSQL_USER = 'mediapp'
CLOUDSQL_PASSWORD = ''
CLOUDSQL_DATABASE = ''
CLOUDSQL_CONNECTION_NAME = ''
LOCAL_SQLALCHEMY_DATABASE_URI = (
    'mysql+pymysql://mediapp:password@127.0.0.1:3306/mediconsult').format (
    nam=CLOUDSQL_USER,
    pas=CLOUDSQL_PASSWORD,
    dbn=CLOUDSQL_DATABASE,
)

LIVE_SQLALCHEMY_DATABASE_URI = (
    'mysql+pymysql://mediapp:password@localhost/mediconsult?unix_socket=/cloudsql/wise-resolver-246504:australia-southeast1:medidata').format (
    nam=CLOUDSQL_USER,
    pas=CLOUDSQL_PASSWORD,
    dbn=CLOUDSQL_DATABASE,
    con=CLOUDSQL_CONNECTION_NAME,
)

if os.environ.get ('GAE_INSTANCE'):
    app.config['SQLALCHEMY_DATABASE_URI'] = LIVE_SQLALCHEMY_DATABASE_URI
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = LOCAL_SQLALCHEMY_DATABASE_URI

# Override to SQLITE (for testing ...)
# SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'


db = SQLAlchemy(app)
socketio = SocketIO(app)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_port'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'REDACTED'
app.config['MAIL_PASSWORD'] = 'REDACTED'
mail = Mail(app)

from mediconsult import routes