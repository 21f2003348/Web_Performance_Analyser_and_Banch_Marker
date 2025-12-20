from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from sqlalchemy import func
from datetime import datetime
import logging
import os
import flask_profiler

from forms import LoginForm, RegistrationForm
from models import db, User, Subject, Chapter, Quiz, Question, Score
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
login_manager = LoginManager()

# existing config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = 'your_secret_key'

# flask_profiler config
app.config["flask_profiler"] = {
    "enabled": True,
    "storage": {
        "engine": "sqlite",
        "FILE": "flask_profiler.sqlite"
    },
    "basicAuth": {
        "enabled": False,
        "username": "admin",
        "password": "admin"
    },
    "ignore": ["/static/*", "/favicon.ico"],
    "endpoint": "flask_profiler"
}

# Initialize extensions BEFORE routes
flask_profiler.init_app(app)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800,
}

db.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


login_manager.init_app(app)


@app.route('/', methods=['GET', 'POST'])
@flask_profiler.profile()
def home():
    return render_template('base.html')


@app.route('/register', methods=['GET', 'POST'])
@flask_profiler.profile()
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            return render_template('register.html', form=form, error="Username already exists.")

        new_user = User(
            username=form.username.data,
            password=generate_password_hash(form.password.data),
            full_name=form.full_name.data,
            qualification=form.qualification.data,
            dob=form.dob.data
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
@flask_profiler.profile()
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None:
            return render_template('login.html', form=form, error="Username not found.")
        elif not check_password_hash(user.password, form.password.data):
            return render_template('login.html', form=form, error="Incorrect password.")
        else:
            session['user_id'] = user.id
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))

    return render_template('login.html', form=form, error=None)


@app.route('/user_dashboard', methods=['GET'])
@flask_profiler.profile()
def user_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    attempted_quiz_ids = Score.query.filter_by(user_id=user_id).with_entities(Score.quiz_id).all()
    attempted_quiz_ids = [quiz_id[0] for quiz_id in attempted_quiz_ids]

    quizzes = Quiz.query.filter(Quiz.id.notin_(attempted_quiz_ids)).all()
    questions = Question.query.all()

    return render_template('user_dashboard.html', user=user, quizzes=quizzes, questions=questions)


@app.route('/user_dashboard_scores', methods=['GET'])
@flask_profiler.profile()
def user_dashboard_scores():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    scores = Score.query.filter_by(user_id=user_id).all()
    user = User.query.get(user_id)

    return render_template('user_dashboard_scores.html', scores=scores, user=user)


@app.route('/view')
@flask_profiler.profile()
def view():
    quiz_id = request.args.get('quiz_id')
    quiz = Quiz.query.get(quiz_id)
    chapter = Chapter.query.get(quiz.chapter_id)
    subject = Subject.query.get(chapter.subject_id)

    user_id = session.get('user_id')
    total_score = Score.query.filter_by(quiz_id=quiz_id, user_id=user_id).first()

    total_score = total_score.total_scored if total_score else None

    return render_template('view.html',
                           quiz=quiz,
                           chapter_name=chapter.name,
                           subject_name=subject.name,
                           total_score=total_score)


@app.route('/quiz/<int:quiz_id>', methods=['GET'])
@flask_profiler.profile()
def quiz(quiz_id):
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template('quiz.html', questions=questions, quiz_id=quiz_id)


@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
@flask_profiler.profile()
def submit_quiz(quiz_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    total_score = 0
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    for question in questions:
        selected_answer = request.form.get(str(question.id))
        if selected_answer and int(selected_answer) == question.correct_answer:
            total_score += 1

    score_entry = Score(
        quiz_id=quiz_id,
        user_id=user_id,
        time_stamp_of_attempt=datetime.now(),
        total_scored=total_score
    )

    db.session.add(score_entry)
    db.session.commit()

    return redirect(url_for('view', quiz_id=quiz_id))


@app.route('/quiz_info/<int:quiz_id>', methods=['GET'])
@flask_profiler.profile()
def quiz_info(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return "Quiz not found", 404

    subject = Subject.query.get(quiz.chapter_id)
    chapter = Chapter.query.get(quiz.chapter_id)

    return render_template(
        'view.html',
        quiz_id=quiz.id,
        subject=subject.name,
        chapter_number=chapter.id,
        scheduled_date=quiz.date_of_quiz,
        duration=quiz.time_duration
    )


@app.route('/admin_dashboard', methods=['GET', 'POST'])
@flask_profiler.profile()
def admin_dashboard():
    if not session.get('user_id') or User.query.get(session['user_id']).role != 'admin':
        return redirect(url_for('login'))

    subjects = Subject.query.all()
    chapters = Chapter.query.all()
    questions = Question.query.all()
    return render_template('admin_dashboard.html', subjects=subjects, chapters=chapters, questions=questions)


@app.route('/admin_dashboard_quiz', methods=['GET', 'POST'])
@flask_profiler.profile()
def admin_dashboard_quiz():
    if not session.get('user_id') or User.query.get(session['user_id']).role != 'admin':
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user = User.query.get(user_id)

    quizes = Quiz.query.all()
    questions = Question.query.all()

    return render_template('admin_dashboard_quiz.html', questions=questions, quizes=quizes, user=user)


@app.route('/admin_dashboard_summary', methods=['GET', 'POST'])
@flask_profiler.profile()
def admin_dashboard_summary():
    if not session.get('user_id') or User.query.get(session['user_id']).role != 'admin':
        return redirect(url_for('login'))

    scores = Score.query.all()
    quiz_attempts = db.session.query(
        Score.quiz_id, func.count(Score.user_id)
    ).group_by(Score.quiz_id).all()

    users = {user.id: user for user in User.query.all()}

    return render_template('admin_dashboard_summary.html',
                           scores=scores,
                           quiz_attempts=quiz_attempts,
                           users=users)


@app.route('/api/quizzes', methods=['POST'])
@flask_profiler.profile()
def api_add_quiz():
    data = request.get_json()
    new_quiz = Quiz(
        chapter_id=data['chapter_id'],
        date_of_quiz=data['date_of_quiz'],
        time_duration=data['time_duration'],
        remarks=data['remarks']
    )
    try:
        db.session.add(new_quiz)
        db.session.commit()
        return jsonify({'message': 'Quiz added successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/api/questions', methods=['POST'])
@flask_profiler.profile()
def api_add_question():
    data = request.get_json()
    new_question = Question(
        quiz_id=data['quiz_id'],
        question_statement=data['question_statement'],
        option1=data['option1'],
        option2=data['option2'],
        option3=data.get('option3', ''),
        option4=data.get('option4', '')
    )
    try:
        db.session.add(new_question)
        db.session.commit()
        return jsonify({'message': 'Question added successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/add_quiz', methods=['GET', 'POST'])
@flask_profiler.profile()
def add_quiz():
    if request.method == 'POST':
        chapter_id = request.form['chapter_id']
        date_of_quiz = datetime.strptime(request.form['date_of_quiz'], '%Y-%m-%d').date()
        time_duration = request.form['time_duration']
        remarks = request.form['remarks']

        new_quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
            remarks=remarks
        )

        try:
            db.session.add(new_quiz)
            db.session.commit()
            return redirect(url_for('admin_dashboard_quiz'))
        except Exception as e:
            db.session.rollback()
            return render_template('add_quiz.html', error=str(e), chapters=Chapter.query.all())

    chapters = Chapter.query.all()
    return render_template('add_quiz.html', chapters=chapters)


@app.route('/delete_question/<int:question_id>', methods=['POST'])
@flask_profiler.profile()
def delete_question(question_id):
    question_to_delete = Question.query.get(question_id)
    if question_to_delete:
        db.session.delete(question_to_delete)
        db.session.commit()

    return redirect(url_for('admin_dashboard_quiz'))


@app.route('/add_question', methods=['GET', 'POST'])
@flask_profiler.profile()
def add_question():
    quiz_id = request.args.get('quiz_id')
    chapter_id = request.args.get('chapter_id')

    if not quiz_id:
        return redirect(url_for('admin_dashboard_quiz'))

    if request.method == 'POST':
        new_question = Question(
            chapter_id=chapter_id,
            quiz_id=quiz_id,
            question_title=request.form['question_title'],
            question_statement=request.form['question_statement'],
            option1=request.form['option1'],
            option2=request.form['option2'],
            option3=request.form.get('option3', ''),
            option4=request.form.get('option4', ''),
            correct_answer=request.form['correct_answer']
        )
        db.session.add(new_question)
        db.session.commit()
        return redirect(url_for('add_question'))

    quizzes = Quiz.query.all()
    return render_template('add_question.html', quizzes=quizzes, quiz_id=quiz_id)


@app.route('/manage_users', methods=['GET', 'POST'])
@flask_profiler.profile()
def manage_users():
    users = User.query.all()
    if request.method == 'POST':
        user_id = request.form['user_id']
        action = request.form['action']

        if action == 'delete':
            user_to_delete = User.query.get(user_id)
            db.session.delete(user_to_delete)
            db.session.commit()

    return render_template('manage_users.html', users=users)


@app.route('/add_subject', methods=['GET', 'POST'])
@flask_profiler.profile()
def add_subject():
    if request.method == 'POST':
        new_subject = Subject(
            name=request.form['name'],
            description=request.form['description']
        )
        db.session.add(new_subject)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    subjects = Subject.query.all()
    return render_template('add_subject.html', subjects=subjects)


@app.route('/add_chapter', methods=['GET', 'POST'])
@flask_profiler.profile()
def add_chapter():
    subject_id = request.args.get('subject_id')
    if not subject_id:
        return "Subject ID is required", 400

    if request.method == 'POST':
        new_chapter = Chapter(
            name=request.form['name'],
            description=request.form['description'],
            subject_id=subject_id
        )
        db.session.add(new_chapter)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('add_chapter.html', subject_id=subject_id)


@app.route('/delete_chapter/<int:chapter_id>', methods=['POST'])
@flask_profiler.profile()
def delete_chapter(chapter_id):
    chapter_to_delete = Chapter.query.get(chapter_id)
    if chapter_to_delete:
        db.session.delete(chapter_to_delete)
        db.session.commit()

    return redirect(url_for('admin_dashboard'))

def seed_default_data():
    """
    Create default seed data (idempotent-ish):
      - 3 subjects
      - 3 chapters per subject
      - 3 quizzes per chapter
      - 3 questions per quiz
      - 3 sample non-admin users
      - some sample scores
    Controlled by env SEED_DB=1
    """
    from werkzeug.security import generate_password_hash
    import logging
    s_logger = logging.getLogger('seed')
    try:
        # Users
        users_data = [
            {"username": "alice@example.com", "password": "alicepass", "full_name": "Alice Example"},
            {"username": "bob@example.com",   "password": "bobpass",   "full_name": "Bob Example"},
            {"username": "carol@example.com", "password": "carolpass", "full_name": "Carol Example"},
        ]
        created_users = []
        for u in users_data:
            existing = User.query.filter_by(username=u["username"]).first()
            if existing:
                created_users.append(existing)
            else:
                new_u = User(
                    username=u["username"],
                    password=generate_password_hash(u["password"]),
                    full_name=u["full_name"],
                    role='user'
                )
                db.session.add(new_u)
                created_users.append(new_u)
        db.session.commit()
        s_logger.info("Users seeded or already present.")

        # Subjects/Chapters/Quizzes/Questions
        for s_i in range(1, 4):
            subj_name = f"Subject {s_i}"
            subj = Subject.query.filter_by(name=subj_name).first()
            if subj:
                continue
            subj = Subject(name=subj_name, description=f"Description for {subj_name}")
            db.session.add(subj)
            db.session.flush()

            for c_i in range(1, 4):
                chap_name = f"{subj_name} - Chapter {c_i}"
                chap = Chapter(name=chap_name,
                               description=f"Description for Chapter {c_i} of {subj_name}",
                               subject_id=subj.id)
                db.session.add(chap)
                db.session.flush()

                for qz_i in range(1, 4):
                    quiz = Quiz(chapter_id=chap.id,
                                date_of_quiz=datetime.utcnow().date(),
                                time_duration="30",
                                remarks=f"Auto-created quiz {qz_i} for chapter {chap.id}")
                    db.session.add(quiz)
                    db.session.flush()

                    for qt_i in range(1, 4):
                        question = Question(
                            chapter_id=chap.id,
                            quiz_id=quiz.id,
                            question_title=f"Q{qt_i} for Quiz {quiz.id}",
                            question_statement=f"What is the sample answer for question {qt_i}?",
                            option1="Option 1",
                            option2="Option 2",
                            option3="Option 3",
                            option4="Option 4",
                            correct_answer=1
                        )
                        db.session.add(question)

        db.session.commit()
        s_logger.info("Subjects/chapters/quizzes/questions seeded.")

        # Scores
        if Score.query.count() == 0:
            all_quizzes = Quiz.query.order_by(Quiz.id).limit(9).all()
            if all_quizzes and created_users:
                for i, quiz in enumerate(all_quizzes):
                    user = created_users[i % len(created_users)]
                    score_val = (i % 4)
                    sc = Score(
                        quiz_id=quiz.id,
                        user_id=user.id,
                        time_stamp_of_attempt=datetime.utcnow(),
                        total_scored=score_val
                    )
                    db.session.add(sc)
                db.session.commit()
                s_logger.info("Sample scores seeded.")
    except Exception:
        db.session.rollback()
        s_logger.exception("Seeding failed; rolled back.")
        raise

if __name__ == '__main__':
    with app.app_context():

        # Remove existing database file if exists
        if os.path.exists('database.db'):
            os.remove('database.db')

        db.create_all()

        # Create admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin'),
                full_name='Admin User',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()

    app.run(debug=True)
