from datetime import datetime
from app import db

class BloodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', name='fk_bloodrequest_hospital_id'), nullable=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_bloodrequest_requester_id'), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    units_needed = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    status = db.Column(db.String(20), default='PENDING')  # PENDING, ACCEPTED, REJECTED, FULFILLED, CANCELLED
    patient_details = db.Column(db.Text)
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deadline = db.Column(db.DateTime)
    
    hospital = db.relationship('Hospital', backref=db.backref('hospital_blood_requests', lazy=True), foreign_keys=[hospital_id])
    requester = db.relationship('User', backref=db.backref('requested_blood_requests', lazy=True), foreign_keys=[requester_id])
    donations = db.relationship('Donation', backref='request', lazy=True)

    def __repr__(self):
        return f'<BloodRequest {self.id} - {self.blood_type}>'

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id', name='fk_donation_donor_id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('blood_request.id', name='fk_donation_request_id'))
    blood_type = db.Column(db.String(5), nullable=False)
    units = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='PENDING')  # PENDING, ACCEPTED, REJECTED, COMPLETED, CANCELLED
    donation_date = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    donor = db.relationship('Donor', backref=db.backref('donations', lazy=True))

    def __repr__(self):
        return f'<Donation {self.id} - {self.blood_type}>'

class BloodInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blood_bank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.id', name='fk_bloodinventory_bloodbank_id'), nullable=False)
    blood_type = db.Column(db.String(5), nullable=False)
    units_available = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    blood_bank = db.relationship('BloodBank', backref=db.backref('inventory', lazy=True))

    def __repr__(self):
        return f'<BloodInventory {self.blood_type} - {self.units_available} units>'

class BloodDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_blooddrive_organizer_id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='UPCOMING')  # UPCOMING, ONGOING, COMPLETED, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    organizer = db.relationship('User', backref=db.backref('organized_drives', lazy=True))
    registrations = db.relationship('DriveRegistration', backref='drive', lazy=True)

    def __repr__(self):
        return f'<BloodDrive {self.title}>'

class DriveRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    drive_id = db.Column(db.Integer, db.ForeignKey('blood_drive.id', name='fk_driveregistration_drive_id'), nullable=False)
    donor_id = db.Column(db.Integer, db.ForeignKey('donor.id', name='fk_driveregistration_donor_id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='REGISTERED')  # REGISTERED, ATTENDED, CANCELLED
    
    donor = db.relationship('Donor', backref=db.backref('drive_registrations', lazy=True))

    def __repr__(self):
        return f'<DriveRegistration {self.id}>' 