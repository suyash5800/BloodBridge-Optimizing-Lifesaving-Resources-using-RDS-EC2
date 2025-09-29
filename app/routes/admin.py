from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, BloodRequest, Donation, BloodInventory, Hospital, Donor, BloodDrive, BloodBank
from app.forms import ApproveRejectForm, BloodDriveForm
from functools import wraps

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get pending blood requests
    pending_requests = BloodRequest.query.filter_by(status='PENDING').order_by(BloodRequest.created_at.desc()).all()
    
    # Get pending donations
    pending_donations = Donation.query.filter_by(status='PENDING').order_by(Donation.created_at.desc()).all()
    
    # Get all blood requests for the table
    blood_requests = BloodRequest.query.order_by(BloodRequest.created_at.desc()).all()
    
    # Get all donations for the table
    donations = Donation.query.order_by(Donation.created_at.desc()).all()
    
    # Get total donors
    total_donors = Donor.query.count()

    blood_drives = BloodDrive.query.order_by(BloodDrive.start_date.desc()).all()
    form = ApproveRejectForm()
    return render_template('admin/dashboard.html', 
                           pending_requests=pending_requests, 
                           pending_donations=pending_donations, 
                           blood_requests=blood_requests,
                           donations=donations,
                           total_donors=total_donors, 
                           blood_drives=blood_drives,
                           form=form)

@bp.route('/blood-request/<int:request_id>/<action>', methods=['POST'])
def manage_blood_request(request_id, action):
    blood_request = BloodRequest.query.get_or_404(request_id)
    form = ApproveRejectForm()
    if form.validate_on_submit():
        blood_request.admin_notes = form.admin_notes.data
        if action == 'accept':
            blood_request.status = 'ACCEPTED'
            # Decrease blood inventory if accepted
            blood_inventory = BloodInventory.query.filter_by(blood_type=blood_request.blood_type).first()
            if blood_inventory:
                blood_inventory.units_available -= blood_request.units_needed
            else:
                # This case should ideally not happen if availability is checked at request creation
                flash('Error: Blood type not found in inventory.', 'error')
                blood_request.status = 'REJECTED' # Revert status if inventory issue
            flash('Blood request accepted.', 'success')
        elif action == 'reject':
            blood_request.status = 'REJECTED'
            flash('Blood request rejected.', 'success')
        db.session.commit()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
    return redirect(url_for('admin.dashboard'))

@bp.route('/donation/<int:donation_id>/<action>', methods=['POST'])
def manage_donation(donation_id, action):
    donation = Donation.query.get_or_404(donation_id)
    form = ApproveRejectForm()
    if form.validate_on_submit():
        donation.admin_notes = form.admin_notes.data
        if action == 'accept':
            donation.status = 'ACCEPTED'
            # Increase blood inventory if accepted
            blood_inventory = BloodInventory.query.filter_by(blood_type=donation.blood_type).first()
            if blood_inventory:
                blood_inventory.units_available += donation.units
            else:
                # Find a blood bank to associate with for new inventory. For now, use the first one found.
                first_blood_bank = BloodBank.query.first()
                if first_blood_bank:
                    new_inventory = BloodInventory(blood_bank_id=first_blood_bank.id, blood_type=donation.blood_type, units_available=donation.units) 
                    db.session.add(new_inventory)
                else:
                    flash('Error: No blood bank found to add inventory to.', 'error')
                    donation.status = 'REJECTED' # Revert status if no blood bank
            flash('Donation accepted.', 'success')
        elif action == 'reject':
            donation.status = 'REJECTED'
            flash('Donation rejected.', 'success')
        db.session.commit()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error in {getattr(form, field).label.text}: {error}", 'error')
    return redirect(url_for('admin.dashboard'))

@bp.route('/schedule_drive', methods=['GET', 'POST'])
def schedule_drive():
    form = BloodDriveForm()
    if form.validate_on_submit():
        new_drive = BloodDrive(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            organizer_id=current_user.id # Assuming admin is the organizer
        )
        db.session.add(new_drive)
        db.session.commit()
        flash('Blood drive scheduled successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/schedule_drive.html', form=form)

@bp.route('/edit_drive/<int:drive_id>', methods=['GET', 'POST'])
def edit_drive(drive_id):
    drive = BloodDrive.query.get_or_404(drive_id)
    form = BloodDriveForm(obj=drive)
    if form.validate_on_submit():
        drive.title = form.title.data
        drive.description = form.description.data
        drive.location = form.location.data
        drive.start_date = form.start_date.data
        drive.end_date = form.end_date.data
        db.session.commit()
        flash('Blood drive updated successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/schedule_drive.html', form=form, drive=drive) # Reusing schedule_drive template

@bp.route('/delete_drive/<int:drive_id>', methods=['POST'])
def delete_drive(drive_id):
    drive = BloodDrive.query.get_or_404(drive_id)
    db.session.delete(drive)
    db.session.commit()
    flash('Blood drive deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard')) 