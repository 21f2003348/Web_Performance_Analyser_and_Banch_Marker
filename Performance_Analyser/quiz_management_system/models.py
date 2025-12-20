from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    qualification = db.Column(db.String(150))
    dob = db.Column(db.Date)
    role = db.Column(db.String(50), default='user') 
    
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500))

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500))
    subject_id = db.Column(db.Integer)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer)
    date_of_quiz = db.Column(db.Date)
    time_duration = db.Column(db.String(10))
    remarks = db.Column(db.String(500), nullable=True) 

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer)
    quiz_id = db.Column(db.Integer)
    question_title = db.Column(db.String(100), nullable=False)
    question_statement = db.Column(db.String(500))
    option1 = db.Column(db.String(150))
    option2 = db.Column(db.String(150))
    option3 = db.Column(db.String(150))
    option4 = db.Column(db.String(150))
    correct_answer = db.Column(db.Integer, nullable=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    time_stamp_of_attempt = db.Column(db.DateTime)
    total_scored = db.Column(db.Integer)