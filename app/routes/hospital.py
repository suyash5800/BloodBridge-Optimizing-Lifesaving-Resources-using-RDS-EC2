from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import BloodRequest, Donation, Hospital, BloodInventory
from datetime import datetime, timedelta

bp = Blueprint('hospital', __name__, url_prefix='/hospital')

@bp.route('/profile')
@login_required
def profile():
    if not isinstance(current_user, Hospital):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    # Get recent blood requests
    recent_requests = BloodRequest.query.filter_by(
        hospital_id=current_user.id
    ).order_by(BloodRequest.created_at.desc()).limit(5).all()
    
    # Get recent donations
    recent_donations = Donation.query.join(BloodRequest).filter(
        BloodRequest.hospital_id == current_user.id,
        Donation.status == 'COMPLETED'
    ).order_by(Donation.donation_date.desc()).limit(5).all()
    
    return render_template('hospital/profile.html',
                         recent_requests=recent_requests,
                         recent_donations=recent_donations)

@bp.route('/blood-requests')
@login_required
def blood_requests():
    if not isinstance(current_user, Hospital):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    requests = BloodRequest.query.filter_by(
        hospital_id=current_user.id
    ).order_by(BloodRequest.created_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)
    
    return render_template('hospital/blood_requests.html', requests=requests)

@bp.route('/create-request', methods=['GET', 'POST'])
@login_required
def create_request():
    if not isinstance(current_user, Hospital):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        blood_type = request.form.get('blood_type')
        units_needed = int(request.form.get('units_needed'))
        priority = request.form.get('priority')
        patient_details = request.form.get('patient_details')
        deadline = datetime.strptime(
            request.form.get('deadline'), '%Y-%m-%d %H:%M')
        
        # Check for blood availability
        blood_inventory = BloodInventory.query.filter_by(blood_type=blood_type).first()
        if not blood_inventory or blood_inventory.units_available < units_needed:
            flash(f'Requested blood group {blood_type} is not available right now or not enough units.', 'error')
            return render_template('hospital/create_request.html')

        request = BloodRequest(
            hospital_id=current_user.id,
            blood_type=blood_type,
            units_needed=units_needed,
            priority=priority,
            patient_details=patient_details,
            deadline=deadline,
            status='PENDING'
        )
        
        db.session.add(request)
        db.session.commit()
        
        flash('Blood request created successfully and is awaiting admin approval!', 'success')
        return redirect(url_for('hospital.blood_requests'))
    
    return render_template('hospital/create_request.html')

@bp.route('/request/<int:id>')
@login_required
def request_detail(id):
    if not isinstance(current_user, Hospital):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    request = BloodRequest.query.get_or_404(id)
    
    if request.hospital_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    # Get donations for this request
    donations = Donation.query.filter_by(
        request_id=request.id
    ).order_by(Donation.donation_date).all()
    
    return render_template('hospital/request_detail.html',
                         request=request,
                         donations=donations)

@bp.route('/cancel-request/<int:id>', methods=['POST'])
@login_required
def cancel_request(id):
    if not isinstance(current_user, Hospital):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    request = BloodRequest.query.get_or_404(id)
    
    if request.hospital_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    if request.status != 'PENDING':
        flash('Cannot cancel a request that is not pending', 'error')
        return redirect(url_for('hospital.request_detail', id=id))
    
    request.status = 'CANCELLED'
    db.session.commit()
    
    flash('Request cancelled successfully', 'success')
    return redirect(url_for('hospital.blood_requests'))

@bp.route('/update-request/<int:id>', methods=['POST'])
@login_required
def update_request(id):
    if not isinstance(current_user, Hospital):
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    request = BloodRequest.query.get_or_404(id)
    
    if request.hospital_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    if request.status != 'PENDING':
        flash('Cannot update a request that is not pending', 'error')
        return redirect(url_for('hospital.request_detail', id=id))
    
    request.units_needed = int(request.form.get('units_needed'))
    request.priority = request.form.get('priority')
    request.patient_details = request.form.get('patient_details')
    request.deadline = datetime.strptime(
        request.form.get('deadline'), '%Y-%m-%d %H:%M')
    
    db.session.commit()
    
    flash('Request updated successfully', 'success')
    return redirect(url_for('hospital.request_detail', id=id)) 