from app import create_app, db
from app.models import User, BloodBank, Hospital, BloodDrive, BloodInventory, Donor, BloodRequest, Admin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def init_db():
    app = create_app()
    with app.app_context():
        # Drop all tables and recreate them (handled by migrations now, but good for dev reset)
        db.drop_all()
        db.create_all()

        # Create sample users
        admin = Admin(
            email='admin@gmail.com',
            password_hash=generate_password_hash('admin@123'),
            first_name='Admin',
            last_name='User',
            is_active=True
        )
        
        blood_bank = BloodBank(
            email='bloodbank@example.com',
            password_hash=generate_password_hash('bank123'),
            first_name='City',
            last_name='Blood Bank',
            bank_name='City Blood Bank',
            license_number='BB-12345',
            emergency_contact='555-0000',
            phone='555-0123',
            address='123 Main St, City',
            is_active=True,
            user_type='blood_bank'
        )
        
        hospital = Hospital(
            email='hospital@example.com',
            password_hash=generate_password_hash('hospital123'),
            first_name='City',
            last_name='Hospital',
            hospital_name='City General Hospital',
            license_number='HOSP-67890',
            emergency_contact='555-1111',
            phone='555-0124',
            address='456 Health Ave, City',
            is_active=True,
            user_type='hospital'
        )
        
        donor = Donor(
            email='donor@example.com',
            password_hash=generate_password_hash('donor123'),
            first_name='John',
            last_name='Doe',
            blood_type='O+',
            is_active=True,
            user_type='donor'
        )

        # Add and commit users first
        db.session.add_all([admin, blood_bank, hospital, donor])
        db.session.commit()

        # Create sample blood inventory
        inventory_o_pos = BloodInventory(
            blood_bank_id=blood_bank.id,
            blood_type='O+',
            units_available=100
        )
        inventory_a_neg = BloodInventory(
            blood_bank_id=blood_bank.id,
            blood_type='A-',
            units_available=50
        )
        inventory_b_pos = BloodInventory(
            blood_bank_id=blood_bank.id,
            blood_type='B+',
            units_available=75
        )
        inventory_ab_pos = BloodInventory(
            blood_bank_id=blood_bank.id,
            blood_type='AB+',
            units_available=20
        )

        # Create sample blood drives
        blood_drive1 = BloodDrive(
            organizer_id=blood_bank.id,
            title='Community Blood Drive',
            location='City Community Center',
            description='Join us for our monthly community blood drive',
            start_date=datetime.now() + timedelta(days=7),
            end_date=datetime.now() + timedelta(days=7, hours=8),
        )
        
        blood_drive2 = BloodDrive(
            organizer_id=blood_bank.id,
            title='Emergency Blood Collection',
            location='City Hospital',
            description='Urgent blood collection for emergency needs',
            start_date=datetime.now() + timedelta(days=3),
            end_date=datetime.now() + timedelta(days=3, hours=6),
        )

        # Create sample blood requests (formerly emergency requests)
        blood_request1 = BloodRequest(
            hospital_id=hospital.id,
            requester_id=hospital.id,
            blood_type='O-',
            units_needed=5,
            priority='CRITICAL',
            patient_details='Emergency surgery patient',
            deadline=datetime.now() + timedelta(hours=24),
            status='PENDING'
        )
        
        blood_request2 = BloodRequest(
            hospital_id=hospital.id,
            requester_id=hospital.id,
            blood_type='A+',
            units_needed=3,
            priority='HIGH',
            patient_details='Trauma patient',
            deadline=datetime.now() + timedelta(hours=48),
            status='PENDING'
        )

        # Add all objects to the session
        db.session.add_all([
            inventory_o_pos, inventory_a_neg, inventory_b_pos, inventory_ab_pos,
            blood_drive1, blood_drive2,
            blood_request1, blood_request2
        ])
        # Commit the changes
        db.session.commit()
        print('Database initialized with sample data!')

if __name__ == '__main__':
    init_db() 