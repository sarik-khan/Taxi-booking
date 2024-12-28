from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Trip, Car
from app import db
from datetime import datetime, timedelta
# from forms import RegisterForm
from flask import abort, send_file

bp = Blueprint('user', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    ongoing_trips = Trip.query.filter_by(
        user_id=current_user.id,
        trip_status='ongoing'
    ).all()
    recent_trips = Trip.query.filter_by(
        user_id=current_user.id
    ).order_by(Trip.created_at.desc()).limit(5).all()
    
    return render_template('user/dashboard.html', 
                         ongoing_trips=ongoing_trips,
                         recent_trips=recent_trips)

# @bp.route('/register', methods=['GET', 'POST'])
# def register():
#     form = RegisterForm()
#     if form.validate_on_submit():
#         # Handle successful form submission logic here
#         flash('Account created successfully!', 'success')
#         return redirect(url_for('auth.login'))
#     return render_template('register.html', form=form)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.phone = request.form.get('phone')
        
        if 'password' in request.form and request.form.get('password'):
            current_user.set_password(request.form.get('password'))
            
        db.session.commit()
        flash('Profile updated successfully', 'success')
        
    return render_template('user/profile.html')

@bp.route('/trips')
@login_required
def trips():
    trips = Trip.query.filter_by(user_id=current_user.id).order_by(Trip.created_at.desc()).all()
    return render_template('user/trips.html', trips=trips)

@bp.route('/trip/<int:trip_id>')
@login_required
def trip_detail(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('user.trips'))
    return render_template('user/trip_detail.html', trip=trip)

@bp.route('/trip/<int:trip_id>/rate', methods=['POST'])
@login_required
def rate_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('user.trips'))
        
    rating = request.form.get('rating')
    review = request.form.get('review')
    
    trip.driver_rating = rating
    trip.review = review
    db.session.commit()
    
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('user.trip_detail', trip_id=trip_id))


@bp.route('/download_bill/<int:trip_id>')
@login_required
def download_bill(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    if trip.user_id != current_user.id:
        abort(403)
    if not trip.bill_path:
        abort(404)
    
    return send_file(trip.bill_path, 
                    as_attachment=True,
                    download_name=f'bill_{trip.id}.pdf')