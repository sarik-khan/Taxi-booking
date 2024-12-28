from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, current_app
from flask_login import login_required, current_user, login_user, logout_user
from functools import wraps
from app.models import User, Car, Trip, Admin
from app import db, login_manager
from datetime import datetime
import os
from app.utils.decorators import admin_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from forms import AdminLoginForm, AdminRegistrationForm

bp = Blueprint('admin', __name__, url_prefix='/admin')



@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_cars = Car.query.count()
    active_trips = Trip.query.filter_by(trip_status='ongoing').count()
    recent_bookings = Trip.query.order_by(Trip.created_at.desc()).limit(10).all()
    
    return render_template('admin/admin_dashboard.html',
                         total_users=total_users,
                         total_cars=total_cars,
                         active_trips=active_trips,
                         recent_bookings=recent_bookings)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))
    
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('admin.dashboard'))
        flash('Invalid username or password', 'danger')
    
    return render_template('admin/admin_login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated and isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))
    
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        admin = Admin(username=form.username.data)
        admin.set_password(form.password.data)
        db.session.add(admin)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('admin.admin_login'))
    
    return render_template('admin/admin_register.html', form=form)
@bp.route('/logout')
@login_required
@admin_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('admin.login'))

@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/admin_users.html', users=users)

@bp.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot modify your own status', 'danger')
        return redirect(url_for('admin.users'))
        
    user.status = 'blocked' if user.status == 'active' else 'active'
    db.session.commit()
    
    flash(f'User {user.name} has been {"blocked" if user.status == "blocked" else "activated"}', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/cars')
@login_required
@admin_required
def cars():
    cars = Car.query.all()
    return render_template('admin/admin_cars.html', cars=cars)

@bp.route('/car/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_car():
    if request.method == 'POST':
        try:
            car = Car(
                name=request.form.get('name'),
                plate_number=request.form.get('plate_number'),
                fuel_type=request.form.get('fuel_type'),
                passenger_capacity=int(request.form.get('passenger_capacity')),
                base_price=float(request.form.get('base_price'))
            )
            db.session.add(car)
            db.session.commit()
            
            flash('Car added successfully', 'success')
            return redirect(url_for('admin.cars'))
        except (ValueError, TypeError):
            flash('Invalid input values provided', 'danger')
            return redirect(url_for('admin.add_car'))
        
    return render_template('admin/admin_cars_add_update.html', car=None)

@bp.route('/car/<int:car_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_car(car_id):
    car = Car.query.get_or_404(car_id)
    
    if request.method == 'POST':
        try:
            car.name = request.form.get('name')
            car.plate_number = request.form.get('plate_number')
            car.fuel_type = request.form.get('fuel_type')
            car.passenger_capacity = int(request.form.get('passenger_capacity'))
            car.base_price = float(request.form.get('base_price'))
            car.status = request.form.get('status')
            
            db.session.commit()
            flash('Car updated successfully', 'success')
            return redirect(url_for('admin.cars'))
        except (ValueError, TypeError):
            flash('Invalid input values provided', 'danger')
            return redirect(url_for('admin.edit_car', car_id=car_id))
        
    return render_template('admin/admin_cars_add_update.html', car=car)

@bp.route('/trips')
@login_required
@admin_required
def trips():
    trips = Trip.query.order_by(Trip.created_at.desc()).all()
    return render_template('admin/trips.html', trips=trips)

@bp.route('/trip/<int:trip_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_trip_status(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    new_status = request.form.get('status')
    
    if new_status == 'completed':
        trip.end_time = datetime.utcnow()
        trip.car.status = 'available'
        try:
            bill_path = generate_bill(trip)
            trip.bill_path = bill_path
        except Exception as e:
            flash('Trip completed but bill generation failed', 'warning')
    
    trip.trip_status = new_status
    db.session.commit()
    
    flash('Trip status updated successfully', 'success')
    return redirect(url_for('admin.trips'))


# function for invoice generatation
def generate_bill(trip):
    # Fetch trip details from the database
    user = trip.user
    car = trip.car
    
    # Ensure the bill directory exists
    bill_directory = "invoices"
    os.makedirs(bill_directory, exist_ok=True)
    
    # Define the bill file name
    bill_filename = f"{bill_directory}/invoice_{trip.id}.pdf"
    
    # Create a PDF canvas
    pdf = canvas.Canvas(bill_filename, pagesize=A4)
    width, height = A4
    
    # Add title
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawCentredString(width / 2, height - 50, "Invoice")
    
    # Add invoice metadata
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 100, f"Invoice ID: {trip.id}")
    pdf.drawString(50, height - 120, f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.drawString(50, height - 140, f"Payment Status: {trip.payment_status.capitalize()}")
    
    # Add user information
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 180, "Customer Details:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(70, height - 200, f"Name: {user.name}")
    pdf.drawString(70, height - 220, f"Phone: {user.phone}")
    pdf.drawString(70, height - 240, f"Email: {user.email}")
    
    # Add trip information
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 280, "Trip Details:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(70, height - 300, f"From: {trip.from_location}")
    pdf.drawString(70, height - 320, f"To: {trip.to_location}")
    pdf.drawString(70, height - 340, f"Start Time: {trip.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    pdf.drawString(70, height - 360, f"End Time: {trip.end_time.strftime('%Y-%m-%d %H:%M:%S') if trip.end_time else 'Ongoing'}")
    pdf.drawString(70, height - 380, f"Amount: ${trip.amount:.2f}")
    
    # Add car information
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 420, "Car Details:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(70, height - 440, f"Car Name: {car.name}")
    pdf.drawString(70, height - 460, f"Plate Number: {car.plate_number}")
    pdf.drawString(70, height - 480, f"Fuel Type: {car.fuel_type}")
    pdf.drawString(70, height - 500, f"Passenger Capacity: {car.passenger_capacity}")
    
    # Add footer
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawCentredString(width / 2, 30, "Thank you for choosing our service!")
    
    # Save the PDF
    pdf.save()
    
    # Update the trip's bill_path in the database
    trip.bill_path = bill_filename
    db.session.commit()
    
    return bill_filename




@bp.route('/peak-hours', methods=['GET', 'POST'])
@login_required
@admin_required
def peak_hours():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start':
            # Set peak hours flag in database or cache
            current_app.config['PEAK_HOURS_ACTIVE'] = True
            flash('Peak hours started', 'success')
        else:
            current_app.config['PEAK_HOURS_ACTIVE'] = False
            flash('Peak hours ended', 'success')
    
    peak_hours_active = current_app.config.get('PEAK_HOURS_ACTIVE', False)
    return render_template('admin/peak_hours.html', peak_hours_active=peak_hours_active)

@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    if request.method == 'POST':
        try:
            current_app.config['INITIAL_FREE_CREDIT'] = float(request.form.get('initial_free_credit'))
            current_app.config['MAX_CREDIT_PER_BOOKING'] = float(request.form.get('max_credit_per_booking'))
            flash('Settings updated successfully', 'success')
        except ValueError:
            flash('Invalid values provided', 'danger')
    
    return render_template('admin/settings.html',
                         initial_free_credit=current_app.config['INITIAL_FREE_CREDIT'],
                         max_credit_per_booking=current_app.config['MAX_CREDIT_PER_BOOKING'])