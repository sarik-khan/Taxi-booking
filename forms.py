from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateTimeField, TextAreaField, FloatField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from datetime import datetime
from app.models import Admin


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AdminLoginForm(FlaskForm):
    username = StringField('Username', 
        validators=[
            DataRequired(),
            Length(min=4, max=80)
        ])
    password = PasswordField('Password', 
        validators=[
            DataRequired()
        ])
    submit = SubmitField('Login')

class AdminRegistrationForm(FlaskForm):
    username = StringField('Username', 
        validators=[
            DataRequired(),
            Length(min=4, max=80)
        ])
    password = PasswordField('Password', 
        validators=[
            DataRequired(),
            Length(min=6, message='Password must be at least 6 characters long')
        ])
    confirm_password = PasswordField('Confirm Password', 
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        admin = Admin.query.filter_by(username=username.data).first()
        if admin:
            raise ValidationError('Username already exists. Please choose a different one.')

class CarForm(FlaskForm):
    name = StringField('Car Name', validators=[DataRequired(), Length(max=100)])
    plate_number = StringField('Plate Number', validators=[DataRequired(), Length(max=20)])
    fuel_type = SelectField('Fuel Type', choices=[('petrol', 'Petrol'), ('diesel', 'Diesel'), ('electric', 'Electric')], validators=[DataRequired()])
    passenger_capacity = IntegerField('Passenger Capacity', validators=[DataRequired()])
    base_price = FloatField('Base Price per Hour', validators=[DataRequired()])
    status = SelectField('Status', choices=[('available', 'Available'), ('booked', 'Booked'), ('maintenance', 'Maintenance')], validators=[DataRequired()])
    submit = SubmitField('Submit')

class TripBookingForm(FlaskForm):
    from_location = StringField('Pickup Location', validators=[DataRequired(), Length(max=200)])
    to_location = StringField('Drop Location', validators=[DataRequired(), Length(max=200)])
    start_time = DateTimeField('Pickup Time', validators=[DataRequired()], format='%Y-%m-%d %H:%M')
    submit = SubmitField('Book Now')

class TripReviewForm(FlaskForm):
    driver_rating = SelectField('Rate your driver', choices=[(str(i), str(i)) for i in range(1, 6)], validators=[DataRequired()])
    review = TextAreaField('Review', validators=[Length(max=500)])
    submit = SubmitField('Submit Review')

class AddressForm(FlaskForm):
    name = StringField('Address Name', validators=[DataRequired(), Length(max=200)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    zipcode = StringField('ZIP Code', validators=[DataRequired(), Length(max=10)])
    submit = SubmitField('Save Address')

class OTPVerificationForm(FlaskForm):
    otp = StringField('Enter OTP', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verify')