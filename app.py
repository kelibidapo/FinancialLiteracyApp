import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app
app = Flask(__name__)

# Configurations
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.secret_key = 'your_secret_key'  # Change this to a secure key in production
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class ContentModule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    module_id = db.Column(db.Integer, db.ForeignKey('content_module.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=False)  # Store options as a newline-separated string
    answer = db.Column(db.String(10), nullable=False)
    module = db.relationship('ContentModule', backref=db.backref('quizzes', lazy=True))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "error")
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the dashboard.", "error")
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    modules = ContentModule.query.all()
    return render_template('dashboard.html', user=user, modules=modules)

@app.route('/modules')
def modules():
    if 'user_id' not in session:
        flash("Please log in to access modules.", "error")
        return redirect(url_for('login'))

    modules = ContentModule.query.all()
    return render_template('modules.html', modules=modules)

@app.route('/module/<int:module_id>')
def view_module(module_id):
    if 'user_id' not in session:
        flash("Please log in to view the module.", "error")
        return redirect(url_for('login'))
    
    module = ContentModule.query.get_or_404(module_id)
    return render_template('view_module.html', module=module)

@app.route('/quizzes/<int:module_id>')
def quizzes(module_id):
    if 'user_id' not in session:
        flash("Please log in to access quizzes.", "error")
        return redirect(url_for('login'))

    module = ContentModule.query.get_or_404(module_id)
    quizzes = Quiz.query.filter_by(module_id=module_id).all()
    return render_template('quizzes.html', module=module, quizzes=quizzes)

@app.route('/quiz/<int:module_id>', methods=['GET', 'POST'])
def quiz(module_id):
    if 'user_id' not in session:
        flash("Please log in to take the quiz.", "error")
        return redirect(url_for('login'))

    module = ContentModule.query.get_or_404(module_id)
    questions = Quiz.query.filter_by(module_id=module_id).all()
    if request.method == 'POST':
        score = 0
        for question in questions:
            user_answer = request.form.get(str(question.id))
            if user_answer and user_answer.lower() == question.answer.lower():
                score += 1
        return render_template('quiz_result.html', score=score, total=len(questions))

    return render_template('quiz.html', module=module, questions=questions)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

# Ensure database is initialized before running
if __name__ == '__main__':
    os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
