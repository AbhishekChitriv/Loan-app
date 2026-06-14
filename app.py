import os
import random
import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from dotenv import load_dotenv
import pickle
import pandas as pd
import numpy as np

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'abhishekchitrio@gmail.com'
app.config['MAIL_PASSWORD'] = 'siye qios xtlz xuxr'
app.config['MAIL_DEFAULT_SENDER'] = 'abhishekchitrio@gmail.com'
app.config['MAIL_DEBUG'] = True

db = SQLAlchemy(app)
mail = Mail()
mail.init_app(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    mobile = db.Column(db.String(15))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

class OTPStore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

with app.app_context():
    db.create_all()

import traceback

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(email, otp):
    # Retrieve config directly from hardcoded values
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender_email = 'abhishekchitrio@gmail.com'
    password = 'siye qios xtlz xuxr'

    try:
        print(f"DEBUG: Direct SMTP Attempt to {email} via {smtp_server}:{smtp_port}")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Your LendSmart AI OTP Verification"
        
        body = f"Your OTP for LendSmart AI is: {otp}. It will expire in 5 minutes."
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        
        print("Email sent successfully via direct SMTP!")
        return True
    except Exception as e:
        print(f"CRITICAL: Direct SMTP Failed: {e}")
        traceback.print_exc()
        return False

@app.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')
    
    otp = str(random.randint(100000, 999999))
    new_otp = OTPStore(email=email, otp=otp)
    db.session.add(new_otp)
    db.session.commit()

    print(f"DEVELOPMENT BYPASS OTP for {email}: {otp}")

    if send_otp_email(email, otp):
        return jsonify({'success': True, 'message': 'OTP sent successfully'})
    return jsonify({'success': True, 'message': f'Failed to send email. Dev Bypass OTP: {otp}'})


@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    mobile = data.get('mobile')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already exists'})

    new_user = User(
        first_name=first_name, 
        last_name=last_name, 
        mobile=mobile, 
        email=email, 
        password=password
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Account created! Please verify with OTP.'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email, password=password).first()
    if not user:
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    if not user.is_verified:
        otp = str(random.randint(100000, 999999))
        new_otp = OTPStore(email=email, otp=otp)
        db.session.add(new_otp)
        db.session.commit()
        print(f"DEVELOPMENT BYPASS OTP for {email}: {otp}")
        send_otp_email(email, otp)
        return jsonify({'success': True, 'needs_verification': True, 'message': f'Account not verified. Dev Bypass OTP: {otp}'})

    session['user_id'] = user.id
    return jsonify({'success': True, 'message': 'Login successful'})

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data received'})
            
        email = data.get('email', '')
        otp_val = data.get('otp', '')
        
        if email is None: email = ''
        if otp_val is None: otp_val = ''
        
        email = str(email).strip()
        otp_val = str(otp_val).strip()

        print(f"DEBUG: Verifying OTP for [{email}] with code [{otp_val}]")

        if not email or not otp_val:
            return jsonify({'success': False, 'message': 'Email and OTP are required'})

        # Find the latest OTP for this email
        stored_otp = OTPStore.query.filter_by(email=email, otp=otp_val).order_by(OTPStore.created_at.desc()).first()
        
        if stored_otp:
            # Check expiry (5 mins)
            now = datetime.datetime.utcnow()
            time_diff = now - stored_otp.created_at
            print(f"DEBUG: Found OTP in DB. Created at: {stored_otp.created_at}, Age: {time_diff.total_seconds()}s")
            
            if time_diff.total_seconds() > 300: # 5 minutes
                print("DEBUG: OTP expired")
                return jsonify({'success': False, 'message': 'OTP expired'})
            
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_verified = True
                db.session.commit()
                session['user_id'] = user.id
                print(f"DEBUG: User {email} verified successfully")
                return jsonify({'success': True, 'message': 'OTP verified successfully'})
            else:
                print(f"DEBUG: OTP is correct but User {email} does not exist in DB yet")
                return jsonify({'success': True, 'otp_valid': True, 'message': 'OTP valid! Please finish registration.'})
        
        print(f"DEBUG: No matching OTP found for {email} and {otp_val}")
        return jsonify({'success': False, 'message': 'Invalid OTP (code mismatch)'})
    except Exception as e:
        print(f"ERROR in verify_otp: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/check_session')
def check_session():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return jsonify({'logged_in': True, 'email': user.email})
    return jsonify({'logged_in': False})

# Load objects
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)

with open('scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)

# encoder.pkl is problematic if it only has ['Yes'], we'll use manual mapping
# but we'll try to load it just in case
try:
    with open('encoder.pkl', 'rb') as f:
        encoder = pickle.load(f)
except:
    encoder = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # Extract features in the correct order
        # ['age', 'gender', 'education', 'self_employed', 'salaried', 'income', 'cibil_score']
        features = [
            float(data['age']),
            1.0 if data['gender'] == 'Male' else 0.0,
            1.0 if data['education'] == 'Graduate' else 0.0,
            1.0 if data['self_employed'] == 'Yes' else 0.0,
            1.0 if data['salaried'] == 'Yes' else 0.0,
            float(data['income']),
            float(data['cibil_score'])
        ]
        
        # Convert to numpy array and reshape for scaling
        features_arr = np.array(features).reshape(1, -1)
        
        # Scale features
        # Note: Scaler expects a DataFrame or numpy array with the same training columns
        # If scaler was trained with feature names, we should pass it a DataFrame
        cols = ['age', 'gender', 'education', 'self_employed', 'salaried', 'income', 'cibil_score']
        features_df = pd.DataFrame(features_arr, columns=cols)
        scaled_features = scaler.transform(features_df)
        
        # Predict
        prediction = model.predict(scaled_features)
        
        # Since it's LinearRegression, the output is a continuous value.
        # It might be 'Loan Amount' or something similar.
        result = float(prediction[0])
        
        return jsonify({
            'success': True,
            'prediction': round(result, 2),
            'message': f"Predicted value: {round(result, 2)}"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

