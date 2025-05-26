from flask import Blueprint, render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User # Import the new User model

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Route for user registration."""
    if current_user.is_authenticated:
        # If already logged in, redirect to admin dashboard
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2') # For password confirmation
        is_admin_str = request.form.get('is_admin') # Checkbox value

        if not username or not email or not password or not password2:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        if password != password2:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different one.', 'danger')
            return redirect(url_for('auth.register'))

        is_admin = (is_admin_str == 'on') # Checkbox value is 'on' if checked

        new_user = User(username=username, email=email, is_admin=is_admin)
        new_user.set_password(password) # Hash the password
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Route for user login."""
    if current_user.is_authenticated:
        # If already logged in, redirect to admin dashboard
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on' # Checkbox value

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Log the user in
        login_user(user, remember=remember_me)
        
        # Redirect to the 'next' page if provided, otherwise to admin dashboard
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('admin.dashboard') # Default redirect after login
        return redirect(next_page)

    return render_template('auth/login.html')

@bp.route('/logout')
@login_required # Requires login to logout
def logout():
    """Route for user logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index')) # Redirect to home page after logout


