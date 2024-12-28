from flask_mail import Message
from app import mail
from flask import current_app

def send_booking_confirmation(user, trip):
    """Send booking confirmation email"""
    msg = Message('Booking Confirmation',
                 sender=current_app.config['MAIL_USERNAME'],
                 recipients=[user.email])
    
    msg.body = f"""
    Dear {user.name},
    
    Your booking has been confirmed:
    
    From: {trip.from_location}
    To: {trip.to_location}
    Date: {trip.start_time.strftime('%Y-%m-%d')}
    Time: {trip.start_time.strftime('%H:%M')}
    Car: {trip.car.name}
    Amount: ${trip.amount}
    
    Thank you for choosing our service!
    """
    
    mail.send(msg)

def send_trip_status_update(trip):
    """Send trip status update email"""
    msg = Message('Trip Status Update',
                 sender=current_app.config['MAIL_USERNAME'],
                 recipients=[trip.user.email])
    
    msg.body = f"""
    Dear {trip.user.name},
    
    Your trip status has been updated to: {trip.trip_status}
    
    Trip Details:
    From: {trip.from_location}
    To: {trip.to_location}
    Date: {trip.start_time.strftime('%Y-%m-%d')}
    
    Thank you for choosing our service!
    """
    
    mail.send(msg)

def send_cancellation_notification(trip):
    """Send trip cancellation notification"""
    msg = Message('Trip Cancellation',
                 sender=current_app.config['MAIL_USERNAME'],
                 recipients=[trip.user.email])
    
    msg.body = f"""
    Dear {trip.user.name},
    
    Your trip has been cancelled.
    
    Trip Details:
    From: {trip.from_location}
    To: {trip.to_location}
    Date: {trip.start_time.strftime('%Y-%m-%d')}
    
    If you did not cancel this trip, please contact support immediately.
    
    Thank you for your understanding.
    """
    
    mail.send(msg)