import random
from flask_mail import Message
from app import mail
from flask import current_app

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    """Send OTP via email"""
    msg = Message('Your OTP for Taxi Booking',
                 sender=current_app.config['MAIL_USERNAME'],
                 recipients=[email])
    msg.body = f'Your OTP is: {otp}\nThis OTP will expire in {current_app.config["OTP_EXPIRY_MINUTES"]} minutes.'
    mail.send(msg)