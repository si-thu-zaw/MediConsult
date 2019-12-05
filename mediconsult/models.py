from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from mediconsult import db, login_manager, app
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class UserRole(db.Model):
    __tablename__= 'userrole'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    description = db.Column(db.String(500))
    users = db.relationship('User', backref='Role', lazy=True)

    def __repr__(self):
        return f"Role('{self.id}', '{self.name}')"

def userrole_query():
    return UserRole.query

class User(db.Model, UserMixin):
    __tablename__= 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.png')
    password = db.Column(db.String(60), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    blocked = db.Column(db.BOOLEAN)
    role = db.Column(db.Integer, db.ForeignKey('userrole.id'), nullable=False)  
    posts = db.relationship('Post', backref='author', lazy=True)
    motds = db.relationship('motd', backref='sender', lazy=True)
    patients = db.relationship('Patient', backref='carer', lazy=True)
    medcases = db.relationship('medcase', backref='poster', lazy=True)
    accesses = db.relationship('Accesshistory', backref='user', lazy=True)
    patient_notes = db.relationship('PatientNotes', backref='notewriter', lazy=True)    
    prescriptions = db.relationship('Prescription', backref='prescribedby', lazy=True)
    referrals = db.relationship('Referral', backref='referrer', lazy=True)
    results = db.relationship('Result', backref='resultuser', lazy=True)
    comments = db.relationship('Comment', backref='commenter', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')
    
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"
#    def __repr__(self):
#        return f"{self.username}"
    

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class motd(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f"Post('{self.title}', '{self.content}', '{self.date}')"

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.Enum('Male','Female'),  nullable=False)
    address = db.Column(db.Text, nullable=True)
    contact_no = db.Column(db.String(30), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medcases = db.relationship('medcase', backref='subject', lazy=True)
    notes = db.relationship('PatientNotes', backref='notepatient', lazy=True)
    accesses = db.relationship('Accesshistory', backref='viewed', lazy=True)
    prescriptions = db.relationship('Prescription', backref='prescribedto', lazy=True)
    referrals = db.relationship('Referral', backref='referralpatient', lazy=True)
    results = db.relationship('Result', backref='resultpatient', lazy=True)
    history = db.relationship('History', backref='historyowner', lazy=True)

    def __repr__(self):
        return f"Post('{self.name}', '{self.dob}')"

class PatientNotes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    def __repr__(self):
        return f"PatientNotes('{self.title}', '{self.date}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medcase_id = db.Column(db.Integer, db.ForeignKey('medcase.id'), nullable=False) 
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"comment('{self.content}', '{self.date}')"

class medcase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False) 
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    comments = db.relationship(Comment, backref='topic', lazy=True)
    
    def __repr__(self):
        return f"medcase('{self.title}', '{self.date}')"


class Accesshistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False) 
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Accesshistory('{self.user_id}', '{self.patient_id}')"

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medication = db.Column(db.String(50))
    frequency = db.Column(db.Enum('OM', 'ON', 'TDS', 'BDS', 'IND', 'PRN'),  nullable=False)
    period = db.Column(db.String(50))
    comment = db.Column(db.String(500))
    date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)


class Referral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

    def __repr__(self):
        return f"Referral('{self.id}', '{self.date}')"

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    comment = db.Column(db.Text, nullable=False)
    result_file = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

    def __repr__(self):
        return f"Referral('{self.id}', '{self.date}')"

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    general = db.Column(db.Text, nullable=False)
    medical = db.Column(db.Text, nullable=False)
    family = db.Column(db.Text, nullable=False)
    personal = db.Column(db.Text, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

    def __repr__(self):
        return f"History('{self.id}', '{self.patient.name}')"