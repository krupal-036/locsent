from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from models import User, create_user, is_signup_enabled 
from extensions import bcrypt

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get_by_username(username)
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            if user.role == 'Admin': return redirect(url_for('main.admin_dashboard'))
            else: return redirect(url_for('main.user_dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password.', 'danger')
            return redirect(url_for('auth.login'))
    return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if not is_signup_enabled():
        flash('User registration is currently disabled by the administrator.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.get_by_username(username)
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.signup'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = create_user(username, hashed_password)
        if new_user:
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('An error occurred during sign up. Please try again.', 'danger')
            return redirect(url_for('auth.signup'))
    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))