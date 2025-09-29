from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Donation, Donor, BloodDrive, DriveRegistration
from datetime import datetime, timedelta

bp = Blueprint('donor', __name__, url_prefix='/donor')

@bp.route('/profile')
@login_required
def profile():
    if not isinstance(current_user, Donor):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    # Get donation history
    donations = Donation.query.filter_by(donor_id=current_user.id)\
        .order_by(Donation.donation_date.desc()).all()
    
    # Get registered blood drives
    registered_drives = DriveRegistration.query.filter_by(
        donor_id=current_user.id,
        status='REGISTERED'
    ).join(BloodDrive).order_by(BloodDrive.start_date).all()
    
    return render_template('donor/profile.html',
                         donations=donations,
                         registered_drives=registered_drives)

@bp.route('/donation-history')
@login_required
def donation_history():
    if not isinstance(current_user, Donor):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    donations = Donation.query.filter_by(donor_id=current_user.id)\
        .order_by(Donation.donation_date.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('donor/donation_history.html', donations=donations)

@bp.route('/schedule-donation', methods=['GET', 'POST'])
@login_required
def schedule_donation():
    if not isinstance(current_user, Donor):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        donation_date = datetime.strptime(
            request.form.get('donation_date'), '%Y-%m-%d')
        
        # Check if donor is eligible
        last_donation = Donation.query.filter_by(
            donor_id=current_user.id,
            status='COMPLETED'
        ).order_by(Donation.donation_date.desc()).first()
        
        if last_donation and (donation_date - last_donation.donation_date).days < 56:
            flash('You must wait 56 days between donations', 'error')
            return redirect(url_for('donor.schedule_donation'))
        
        donation = Donation(
            donor_id=current_user.id,
            blood_type=current_user.blood_type,
            donation_date=donation_date,
            status='PENDING'
        )
        
        db.session.add(donation)
        db.session.commit()
        
        flash('Donation scheduled successfully and is awaiting admin approval!', 'success')
        return redirect(url_for('donor.donation_history'))
    
    return render_template('donor/schedule_donation.html')

@bp.route('/register-drive/<int:drive_id>', methods=['POST'])
@login_required
def register_for_drive(drive_id):
    if not current_user.is_donor:
        flash('Only donors can register for blood drives.', 'error')
        return redirect(url_for('main.index'))
    
    drive = BloodDrive.query.get_or_404(drive_id)
    
    # Check if already registered
    existing_registration = DriveRegistration.query.filter_by(
        donor_id=current_user.id,
        blood_drive_id=drive_id
    ).first()
    
    if existing_registration:
        flash('You are already registered for this blood drive.', 'info')
        return redirect(url_for('main.blood_drive_detail', id=drive_id))
    
    # Create new registration
    registration = DriveRegistration(
        donor_id=current_user.id,
        blood_drive_id=drive_id,
        notes=request.form.get('notes', '')
    )
    
    try:
        db.session.add(registration)
        db.session.commit()
        flash('Successfully registered for the blood drive!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error registering for blood drive: {str(e)}', 'error')
    
    return redirect(url_for('main.blood_drive_detail', id=drive_id))

@bp.route('/cancel-registration/<int:registration_id>', methods=['POST'])
@login_required
def cancel_registration(registration_id):
    if not current_user.is_donor:
        flash('Only donors can cancel registrations.', 'error')
        return redirect(url_for('main.index'))
    
    registration = DriveRegistration.query.get_or_404(registration_id)
    
    # Verify ownership
    if registration.donor_id != current_user.id:
        flash('You can only cancel your own registrations.', 'error')
        return redirect(url_for('main.index'))
    
    try:
        registration.status = 'cancelled'
        db.session.commit()
        flash('Registration cancelled successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling registration: {str(e)}', 'error')
    
    return redirect(url_for('main.blood_drive_detail', id=registration.blood_drive_id)) 