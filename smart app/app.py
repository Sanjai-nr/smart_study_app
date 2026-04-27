import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    last_reviewed = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.Integer, default=0)

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer, default=0)

class QuizRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Integer)

# Routes
@app.route('/')
def index():
    print(">>> ACCESSING INDEX")
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    print(">>> ACCESSING LOGIN")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except:
            flash('Username already exists')
    return render_template('register.html')

from utils.ocr import process_file
from utils.quiz_generator import generate_quiz

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    print(">>> ACCESSING DASHBOARD")
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file:
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process OCR
            extracted_text = process_file(file_path)
            print(f">>> OCR EXTRACTED TEXT: {extracted_text[:200]}...")
            
            # Save note to DB
            new_note = Note(user_id=user_id, content=extracted_text)
            db.session.add(new_note)
            db.session.commit()
            
            # Generate Quiz
            quiz_data = generate_quiz(extracted_text)
            print(f">>> GENERATED {len(quiz_data)} QUESTIONS")
            session['last_quiz'] = quiz_data
            
            flash('Notes processed successfully!')
            return redirect(url_for('quiz'))

    # Calculate Stats
    notes = Note.query.filter_by(user_id=user_id).all()
    quizzes_count = QuizRecord.query.filter_by(user_id=user_id).count()
    total_minutes = db.session.query(db.func.sum(StudySession.duration_minutes)).filter(StudySession.user_id == user_id).scalar() or 0
    focus_hours = round(total_minutes / 60, 1)
    
    active_session = StudySession.query.filter_by(user_id=user_id, end_time=None).first()

    return render_template('dashboard.html', 
                          notes=notes, 
                          quizzes_count=quizzes_count, 
                          focus_hours=focus_hours,
                          active_session=active_session)

@app.route('/start_session')
def start_session():
    if 'user_id' in session:
        # Check if already has an active session
        existing = StudySession.query.filter_by(user_id=session['user_id'], end_time=None).first()
        if not existing:
            new_session = StudySession(user_id=session['user_id'])
            db.session.add(new_session)
            db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/stop_session')
def stop_session():
    if 'user_id' in session:
        active = StudySession.query.filter_by(user_id=session['user_id'], end_time=None).first()
        if active:
            active.end_time = datetime.utcnow()
            diff = active.end_time - active.start_time
            active.duration_minutes = int(diff.total_seconds() / 60)
            db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/quiz_complete')
def quiz_complete():
    if 'user_id' in session:
        record = QuizRecord(user_id=session['user_id'])
        db.session.add(record)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/quiz')
def quiz():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    quiz_data = session.get('last_quiz', [])
    return render_template('quiz.html', quiz=quiz_data)

@app.route('/notes')
def notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_notes = Note.query.filter_by(user_id=session['user_id']).all()
    return render_template('notes.html', notes=user_notes)

from utils.revision_logic import get_revision_schedule

@app.route('/revision')
def revision():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_notes = Note.query.filter_by(user_id=session['user_id']).all()
    due_notes = get_revision_schedule(user_notes)
    return render_template('revision.html', notes=due_notes)

@app.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({"response": "Please login first"}), 401
    
    data = request.json
    query = data.get('query', '').lower()
    
    user_notes = Note.query.filter_by(user_id=session['user_id']).all()
    
    # Improved search logic
    response_text = "I couldn't find that specific info in your current notes. Try uploading more materials or checking your spelling!"
    
    query_words = [w for w in query.split() if len(w) > 3] # Search for significant words
    
    for note in user_notes:
        content_lower = note.content.lower()
        # Direct match first
        if query in content_lower:
            sentences = note.content.split('.')
            for sentence in sentences:
                if query in sentence.lower():
                    return jsonify({"response": f"According to your notes: \"{sentence.strip()}.\""})
        
        # Keyword match fallback
        for word in query_words:
            if word in content_lower:
                sentences = note.content.split('.')
                for sentence in sentences:
                    if word in sentence.lower():
                        return jsonify({"response": f"I found a mention of '{word}' in your notes: \"{sentence.strip()}.\""})
            
    return jsonify({"response": response_text})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, port=8080)
