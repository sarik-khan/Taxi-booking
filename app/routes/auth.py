from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required
from app.models import User
from forms import LoginForm
from app import db
from app.utils.otp import generate_otp, send_otp_email
import random

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
            
        user = User(name=name, email=email, phone=phone)
        user.set_password(password)
        user.free_credit = 500  # Initial free credit
        
        # Generate and send OTP
        otp = generate_otp()
        send_otp_email(email, otp)
        
        # Save OTP in session
        session['registration_otp'] = otp
        session['temp_user'] = {
            'name': name,
            'email': email,
            'phone': phone,
            'password': password
        }
        
        return redirect(url_for('auth.verify_otp'))
        
    return render_template('auth/register.html')

@bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        stored_otp = session.get('registration_otp')
        
        if entered_otp == stored_otp:
            user_data = session.get('temp_user')
            user = User(**user_data)
            user.is_verified = True
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        flash('Invalid OTP', 'danger')
        
    return render_template('auth/verify_otp.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.status == 'blocked':
                flash('Your account has been blocked. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
                
            if not user.is_verified:
                flash('Please verify your email first.', 'warning')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            return redirect(url_for('user.dashboard'))
            
        flash('Invalid email or password', 'danger')
        
    return render_template('auth/login.html', form = form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))