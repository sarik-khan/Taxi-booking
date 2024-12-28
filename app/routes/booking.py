from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Trip, Car
from app import db
from datetime import datetime, timedelta
from app.utils.price import calculate_trip_price

bp = Blueprint('booking', __name__)

@bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    if request.method == 'POST':
        from_location = request.form.get('from_location')
        to_location = request.form.get('to_location')
        start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        
        session['booking_details'] = {
            'from_location': from_location,
            'to_location': to_location,
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M')
        }
        
        return redirect(url_for('booking.select_car'))
        
    return render_template('booking/book.html')

@bp.route('/select-car')
@login_required
def select_car():
    booking_details = session.get('booking_details')
    if not booking_details:
        return redirect(url_for('booking.book'))
        
    available_cars = Car.query.filter_by(status='available').all()
    
    # Calculate price for each car
    cars_with_price = []
    for car in available_cars:
        price = calculate_trip_price(
            car,
            booking_details['from_location'],
            booking_details['to_location']
        )
        cars_with_price.append({
            'car': car,
            'price': price
        })
    
    return render_template('booking/select_car.html', 
                         cars=cars_with_price,
                         booking_details=booking_details)

@bp.route('/confirm-booking/<int:car_id>', methods=['GET', 'POST'])
@login_required
def confirm_booking(car_id):
    booking_details = session.get('booking_details')
    if not booking_details:
        return redirect(url_for('booking.book'))
        
    car = Car.query.get_or_404(car_id)
    price = calculate_trip_price(
        car,
        booking_details['from_location'],
        booking_details['to_location']
    )
    
    if request.method == 'POST':
        # Check if user has enough free credit
        if current_user.free_credit >= price:
            current_user.free_credit -= price
            
        trip = Trip(
            user_id=current_user.id,
            car_id=car_id,
            from_location=booking_details['from_location'],
            to_location=booking_details['to_location'],
            start_time=datetime.strptime(booking_details['start_time'], '%Y-%m-%dT%H:%M'),
            amount=price
        )
        
        car.status = 'booked'
        db.session.add(trip)
        db.session.commit()
        
        # Clear session
        session.pop('booking_details', None)
        
        flash('Booking confirmed successfully!', 'success')
        return redirect(url_for('user.trip_detail', trip_id=trip.id))
        
    return render_template('booking/confirm.html',
                         car=car,
                         price=price,
                         booking_details=booking_details)

@bp.route('/cancel-trip/<int:trip_id>', methods=['POST'])
@login_required
def cancel_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('user.trips'))
        
    # Check if cancellation is within time limit
    if datetime.utcnow() > trip.start_time - timedelta(hours=1):
        flash('Cancellation is only allowed up to 1 hour before trip start', 'danger')
        return redirect(url_for('user.trip_detail', trip_id=trip_id))
        
    trip.trip_status = 'cancelled'
    trip.canceled_by = 'user'
    trip.car.status = 'available'
    
    # Refund free credit if used
    if trip.amount <= current_user.free_credit:
        current_user.free_credit += trip.amount
        
    db.session.commit()
    
    flash('Trip cancelled successfully', 'success')
    return redirect(url_for('user.trips'))