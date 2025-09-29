from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import BloodInventory, Donation, BloodDrive, BloodBank
from datetime import datetime, timedelta

bp = Blueprint('blood_bank', __name__, url_prefix='/blood-bank')

@bp.route('/profile')
@login_required
def profile():
    if not isinstance(current_user, BloodBank):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    # Get current inventory
    inventory = BloodInventory.query.filter_by(
        blood_bank_id=current_user.id
    ).all()
    
    # Get low stock alerts
    low_stock = [item for item in inventory if item.units_available < 10]
    
    # Get recent donations
    recent_donations = Donation.query.filter(
        Donation.status == 'COMPLETED',
        Donation.donation_date > datetime.utcnow() - timedelta(days=7)
    ).order_by(Donation.donation_date.desc()).limit(5).all()
    
    return render_template('blood_bank/profile.html',
                         inventory=inventory,
                         low_stock=low_stock,
                         recent_donations=recent_donations)

@bp.route('/inventory')
@login_required
def inventory():
    if not isinstance(current_user, BloodBank):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    inventory = BloodInventory.query.filter_by(
        blood_bank_id=current_user.id
    ).all()
    
    return render_template('blood_bank/inventory.html', inventory=inventory)

@bp.route('/update-inventory', methods=['POST'])
@login_required
def update_inventory():
    if not isinstance(current_user, BloodBank):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    blood_type = request.form.get('blood_type')
    units = int(request.form.get('units'))
    
    inventory = BloodInventory.query.filter_by(
        blood_bank_id=current_user.id,
        blood_type=blood_type
    ).first()
    
    if inventory:
        inventory.units_available = units
    else:
        inventory = BloodInventory(
            blood_bank_id=current_user.id,
            blood_type=blood_type,
            units_available=units
        )
        db.session.add(inventory)
    
    db.session.commit()
    
    flash('Inventory updated successfully', 'success')
    return redirect(url_for('blood_bank.inventory'))

@bp.route('/blood-drives')
@login_required
def blood_drives():
    if not isinstance(current_user, BloodBank):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    drives = BloodDrive.query.filter_by(
        organizer_id=current_user.id
    ).order_by(BloodDrive.start_date.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('blood_bank/blood_drives.html', drives=drives)

@bp.route('/create-drive', methods=['GET', 'POST'])
@login_required
def create_drive():
    if not isinstance(current_user, BloodBank):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        start_date = datetime.strptime(
            request.form.get('start_date'), '%Y-%m-%d %H:%M')
        end_date = datetime.strptime(
            request.form.get('end_date'), '%Y-%m-%d %H:%M')
        
        drive = BloodDrive(
            organizer_id=current_user.id,
            title=title,
            description=description,
            location=location,
            start_date=start_date,
            end_date=end_date,
            status='UPCOMING'
        )
        
        db.session.add(drive)
        db.session.commit()
        
        flash('Blood drive created successfully!', 'success')
        return redirect(url_for('blood_bank.blood_drives'))
    
    return render_template('blood_bank/create_drive.html')

@bp.route('/drive/<int:id>')
@login_required
def drive_detail(id):
    if not isinstance(current_user, BloodBank):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    drive = BloodDrive.query.get_or_404(id)
    
    if drive.organizer_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    # Get registrations for this drive
    registrations = drive.registrations
    
    return render_template('blood_bank/drive_detail.html',
                         drive=drive,
                         registrations=registrations)

@bp.route('/update-drive/<int:id>', methods=['POST'])
@login_required
def update_drive(id):
    if not isinstance(current_user, BloodBank):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    drive = BloodDrive.query.get_or_404(id)
    
    if drive.organizer_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    drive.title = request.form.get('title')
    drive.description = request.form.get('description')
    drive.location = request.form.get('location')
    drive.start_date = datetime.strptime(
        request.form.get('start_date'), '%Y-%m-%d %H:%M')
    drive.end_date = datetime.strptime(
        request.form.get('end_date'), '%Y-%m-%d %H:%M')
    drive.status = request.form.get('status')
    
    db.session.commit()
    
    flash('Blood drive updated successfully', 'success')
    return redirect(url_for('blood_bank.drive_detail', id=id))

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['blood_bank', 'admin']:
        flash('Access denied. Only blood bank users and admins can access this dashboard.', 'error')
        return redirect(url_for('main.index'))
    
    # Get statistics
    total_drives = BloodDrive.query.filter_by(blood_bank_id=current_user.id).count()
    upcoming_drives = BloodDrive.query.filter(
        BloodDrive.blood_bank_id == current_user.id,
        BloodDrive.start_date > datetime.utcnow()
    ).count()
    total_donations = Donation.query.join(BloodDrive).filter(
        BloodDrive.blood_bank_id == current_user.id
    ).count()
    
    # Get recent drives
    recent_drives = BloodDrive.query.filter_by(
        blood_bank_id=current_user.id
    ).order_by(BloodDrive.start_date.desc()).limit(5).all()
    
    return render_template('blood_bank/dashboard.html',
                         total_drives=total_drives,
                         upcoming_drives=upcoming_drives,
                         total_donations=total_donations,
                         recent_drives=recent_drives)

@bp.route('/edit-drive/<int:drive_id>', methods=['GET', 'POST'])
@login_required
def edit_drive(drive_id):
    drive = BloodDrive.query.get_or_404(drive_id)
    
    if current_user.role == 'blood_bank' and drive.blood_bank_id != current_user.id:
        flash('You are not authorized to edit this blood drive.', 'error')
        return redirect(url_for('blood_bank.dashboard'))
    elif current_user.role == 'admin':
        pass # Admins can edit any drive
    else:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        try:
            drive.title = request.form['title']
            drive.location = request.form['location']
            drive.description = request.form['description']
            drive.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M')
            drive.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M')
            drive.target_donors = int(request.form['target_donors'])
            drive.blood_types_needed = ', '.join(request.form.getlist('blood_types'))
            drive.requirements = request.form['requirements']
            drive.notes = request.form['notes']
            
            db.session.commit()
            flash('Blood drive updated successfully!', 'success')
            return redirect(url_for('blood_bank.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating blood drive: {str(e)}', 'error')
    
    # Convert comma-separated string back to list for pre-selecting options in the form
    drive.blood_types_needed_list = drive.blood_types_needed.split(', ') if drive.blood_types_needed else []
    
    return render_template('blood_bank/schedule_drive.html', drive=drive, is_edit=True)

@bp.route('/delete-drive/<int:drive_id>', methods=['POST'])
@login_required
def delete_drive(drive_id):
    drive = BloodDrive.query.get_or_404(drive_id)
    
    if current_user.role == 'blood_bank' and drive.blood_bank_id != current_user.id:
        flash('You are not authorized to delete this blood drive.', 'error')
        return redirect(url_for('blood_bank.dashboard'))
    elif current_user.role == 'admin':
        pass # Admins can delete any drive
    else:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))

    try:
        db.session.delete(drive)
        db.session.commit()
        flash('Blood drive deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting blood drive: {str(e)}', 'error')
    
    return redirect(url_for('blood_bank.dashboard'))

@bp.route('/schedule-drive', methods=['GET', 'POST'])
@login_required
def schedule_drive():
    if current_user.role not in ['blood_bank', 'admin']:
        flash('Only blood bank users and admins can schedule drives.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            # Create new blood drive
            drive = BloodDrive(
                title=request.form['title'],
                location=request.form['location'],
                description=request.form['description'],
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M'),
                end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M'),
                target_donors=int(request.form['target_donors']),
                blood_types_needed=', '.join(request.form.getlist('blood_types')),
                requirements=request.form['requirements'],
                notes=request.form['notes'],
                blood_bank_id=current_user.id,
                status='scheduled'
            )
            
            db.session.add(drive)
            db.session.commit()
            
            flash('Blood drive scheduled successfully!', 'success')
            return redirect(url_for('blood_bank.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error scheduling blood drive: {str(e)}', 'error')
    
    return render_template('blood_bank/schedule_drive.html') 