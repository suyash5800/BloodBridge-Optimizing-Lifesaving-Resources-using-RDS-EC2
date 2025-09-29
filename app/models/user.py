from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    user_type = db.Column(db.String(20))  # donor, hospital, blood_bank
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Polymorphic relationship
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': user_type
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_notification_count(self):
        from app.models.blood import BloodRequest, Donation
        if self.user_type == 'admin':
            # Count pending blood requests and donations
            pending_requests = BloodRequest.query.filter_by(status='PENDING').count()
            pending_donations = Donation.query.filter_by(status='PENDING').count()
            return pending_requests + pending_donations
        elif self.user_type == 'hospital':
            # Count pending donations for this hospital's requests
            return Donation.query.join(BloodRequest).filter(
                BloodRequest.hospital_id == self.id,
                Donation.status == 'PENDING'
            ).count()
        elif self.user_type == 'blood_bank':
            # Count pending donations for this blood bank's drives
            return Donation.query.join(BloodRequest).join(BloodDrive).filter(
                BloodDrive.organizer_id == self.id,
                Donation.status == 'PENDING'
            ).count()
        elif self.user_type == 'donor':
            # Count pending donations by this donor
            return Donation.query.filter_by(
                donor_id=self.id,
                status='PENDING'
            ).count()
        return 0

    def __repr__(self):
        return f'<User {self.email}>'

class Donor(User):
    __tablename__ = 'donor'
    id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_donor_user_id'), primary_key=True)
    blood_type = db.Column(db.String(5))
    last_donation = db.Column(db.DateTime)
    medical_conditions = db.Column(db.Text)
    emergency_contact = db.Column(db.String(200))
    
    __mapper_args__ = {
        'polymorphic_identity': 'donor',
    }

class Hospital(User):
    __tablename__ = 'hospital'
    id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_hospital_user_id'), primary_key=True)
    hospital_name = db.Column(db.String(100))
    license_number = db.Column(db.String(50))
    emergency_contact = db.Column(db.String(200))
    
    __mapper_args__ = {
        'polymorphic_identity': 'hospital',
    }

class BloodBank(User):
    __tablename__ = 'blood_bank'
    id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_bloodbank_user_id'), primary_key=True)
    bank_name = db.Column(db.String(100))
    license_number = db.Column(db.String(50))
    emergency_contact = db.Column(db.String(200))
    
    __mapper_args__ = {
        'polymorphic_identity': 'blood_bank',
    }

class Admin(User):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_admin_user_id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity': 'admin',
    }

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id)) 