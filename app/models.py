from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    role = db.Column(db.String(20), nullable=False)  # admin, donor, blood_bank, hospital
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Donor specific fields
    blood_type = db.Column(db.String(5))
    last_donation_date = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BloodBank(User):
    __tablename__ = 'blood_bank'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<BloodBank {self.name}>'

class Hospital(User):
    __tablename__ = 'hospital'
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<Hospital {self.name}>'

class EmergencyRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blood_type = db.Column(db.String(5), nullable=False)
    units_needed = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    patient_details = db.Column(db.Text, nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')  # active, fulfilled, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=True)  # Allow None for blood seekers

    hospital = db.relationship('Hospital', backref=db.backref('emergency_requests', lazy=True))

    def __repr__(self):
        return f'<EmergencyRequest {self.blood_type} - {self.units_needed} units>'

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blood_drive_id = db.Column(db.Integer, db.ForeignKey('blood_drive.id'), nullable=True)
    blood_request_id = db.Column(db.Integer, db.ForeignKey('blood_request.id'), nullable=True)
    donation_date = db.Column(db.DateTime, default=datetime.utcnow)
    blood_type = db.Column(db.String(5), nullable=False)
    units = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    notes = db.Column(db.Text)
    
    # Relationships
    donor = db.relationship('User', backref=db.backref('donations', lazy=True))
    blood_request = db.relationship('BloodRequest', backref=db.backref('donations', lazy=True))
    
    def __repr__(self):
        return f'<Donation {self.donor.email} - {self.blood_type}>'

class BloodDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    target_donors = db.Column(db.Integer, nullable=False)
    blood_types_needed = db.Column(db.String(100))  # Comma-separated list of blood types
    requirements = db.Column(db.Text)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blood_bank = db.relationship('User', backref=db.backref('blood_drives', lazy=True))
    registrations = db.relationship('DriveRegistration', backref='blood_drive', lazy=True)
    donations = db.relationship('Donation', backref='blood_drive', lazy=True)
    
    def __repr__(self):
        return f'<BloodDrive {self.title}>'
    
    @property
    def is_upcoming(self):
        return self.start_date > datetime.utcnow()
    
    @property
    def is_completed(self):
        return self.end_date < datetime.utcnow()
    
    @property
    def registration_count(self):
        return len(self.registrations)
    
    @property
    def donation_count(self):
        return len(self.donations)
    
    @property
    def progress_percentage(self):
        if self.target_donors == 0:
            return 0
        return min(100, (self.donation_count / self.target_donors) * 100)

class DriveRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blood_drive_id = db.Column(db.Integer, db.ForeignKey('blood_drive.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='registered')  # registered, confirmed, cancelled
    notes = db.Column(db.Text)
    
    # Relationships
    donor = db.relationship('User', backref=db.backref('drive_registrations', lazy=True))
    
    def __repr__(self):
        return f'<DriveRegistration {self.donor.name} - {self.blood_drive.title}>'
    
    @property
    def is_confirmed(self):
        return self.status == 'confirmed'
    
    @property
    def is_cancelled(self):
        return self.status == 'cancelled'

class BloodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    units_needed = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    status = db.Column(db.String(20), default='PENDING')  # PENDING, FULFILLED, CANCELLED
    patient_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline = db.Column(db.DateTime)

    hospital = db.relationship('Hospital', backref=db.backref('blood_requests', lazy=True))

    def __repr__(self):
        return f'<BloodRequest {self.id} - {self.blood_type}>'

class BloodInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.id'), nullable=True)
    blood_type = db.Column(db.String(5), nullable=False)
    units_available = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blood_bank = db.relationship('BloodBank', backref=db.backref('inventory', lazy=True))

    def __repr__(self):
        return f'<BloodInventory {self.blood_type} - {self.units_available} units>' 