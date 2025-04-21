from flask import render_template, redirect, request, jsonify, url_for, flash
from app import app
from app.forms import TodoForm, LoginForm, RegistrationForm
import sqlalchemy as sa
from app.models import Todo, User, Guest
from app import db
from flask_login import current_user, login_user, logout_user, login_required
from functools import wraps
from urllib.parse import urlsplit


def login_required_or_guest(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow access if the user is authenticated or is a guest
        if not current_user.is_authenticated and not getattr(current_user, 'is_guest', False):
            return redirect(url_for('login'))  # Redirect to login if neither authenticated nor guest
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['POST', 'GET'])
@login_required_or_guest
def home():
    form = TodoForm()
    if request.method == 'POST':
        todo_text = form.todo.data  # Get the todo text only when the form is submitted
        if todo_text:  # Check if the todo_text is not empty
            try:
                if current_user.is_authenticated and not getattr(current_user, 'is_guest', False):
                    new_todo = Todo(text=todo_text, user_id=current_user.id)
                    db.session.add(new_todo)
                    db.session.commit()
                    return redirect(url_for('home'))
                else:
                    flash('Guests cannot add server todos. Please login to save your todos.')
                    return redirect(url_for('home'))
            except Exception as e:
                db.session.rollback()
                print(e)
                flash('There was an issue adding your todo.')
                return redirect(url_for('home'))
        else:
            flash("Todo text cannot be empty")
            return redirect(url_for('home'))  # Return to home if todo is empty
    else:
        if current_user.is_authenticated and not getattr(current_user, 'is_guest', False):
            todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.date_created).all()
        else:
            todos = []
        return render_template("index.html", title="Home", form=form, todos=todos, logged_in=current_user.is_authenticated)


@app.route('/todo_list/<list_id>')
@login_required_or_guest
def todo_list(list_id):
    return render_template("todo_list.html", list_id = list_id)

@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    if todo.user_id != current_user.id:
        flash('You are not authorized to delete this todo.', 'danger')
        return redirect(url_for('index'))

    db.session.delete(todo)
    db.session.commit()
    flash('Todo deleted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/chronometer/<int:todo_id>')
@login_required_or_guest
def chronometer(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    return render_template("chronometer.html", title="Chronometer", todo=todo)

@app.route('/guest_chronometer/<int:guest_id>')
def guest_chronometer(guest_id):
    return render_template('guest_chronometer.html', guest_id=guest_id)


@app.route('/update_time/<int:todo_id>', methods=['POST'])
@login_required_or_guest
def update_time(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    new_time = request.json.get('time')
    if isinstance(new_time, int):
        todo.time = new_time
        db.session.commit()
        return jsonify({"status": "success"}), 200
    return jsonify({"error": "Invalid time"}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.get_id()!='guest':
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            return redirect(url_for('home'))
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/guest_login', methods=['POST'])
def guest_login():
    guest_user = Guest()
    login_user(guest_user)
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated and current_user.get_id()!='guest':
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)