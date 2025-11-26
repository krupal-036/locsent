from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, Response, send_file
from flask_login import login_required, current_user
from models import (
    get_all_users, get_user_location_history, log_location,
    get_all_users_latest_location, check_geofence, get_user_logs_for_export,
    get_geofences, delete_user, is_signup_enabled, set_signup_status
)
from decorators import admin_required
import csv
import io
from fpdf import FPDF

main = Blueprint('main', __name__)

class PDF(FPDF):
    def header(self): self.set_font('Helvetica', 'B', 12); self.cell(0, 10, 'LocSent Location History', 0, 1, 'C')
    def footer(self): self.set_y(-15); self.set_font('Helvetica', 'I', 8); self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'Admin': return redirect(url_for('main.admin_dashboard'))
        return redirect(url_for('main.user_dashboard'))
    return render_template('login.html')
@main.route('/user/dashboard')
@login_required
def user_dashboard(): return render_template('user_dashboard.html', user=current_user)
@main.route('/user/send_location', methods=['POST'])
@login_required
def send_location():
    data = request.json
    if request.headers.getlist("X-Forwarded-For"): ip_address = request.headers.getlist("X-Forwarded-For")[0]
    else: ip_address = request.remote_addr
    success = log_location(user_page_id=current_user.page_id, latitude=data.get('latitude'), longitude=data.get('longitude'), ip_address=ip_address, battery=data.get('battery'), device_info=data.get('deviceInfo'))
    if success:
        if data.get('latitude') and data.get('longitude'):
            status = check_geofence(data.get('latitude'), data.get('longitude'))
            if status: flash(f"GEOFENCE ALERT: User '{current_user.username}' {status}", 'warning')
        return jsonify({'status': 'success', 'message': 'Location logged successfully!'})
    else: return jsonify({'status': 'error', 'message': 'Failed to log location. Check server logs.'}), 500

@main.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    users = get_all_users()
    signup_status = is_signup_enabled()
    return render_template('admin_dashboard.html', users=users, signup_enabled=signup_status)

@main.route('/admin/delete_user/<user_page_id>', methods=['POST'])
@login_required
@admin_required
def delete_user_route(user_page_id):
    success = delete_user(user_page_id)
    if success:
        flash('User successfully deleted.', 'success')
    else:
        flash('Error: Could not delete user.', 'danger')
    return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/toggle_signup', methods=['POST'])
@login_required
@admin_required
def toggle_signup():
    current_status = is_signup_enabled()
    new_status = not current_status
    success = set_signup_status(new_status)
    if success:
        flash(f'User sign-up has been {"enabled" if new_status else "disabled"}.', 'success')
    else:
        flash('Error: Could not update sign-up status.', 'danger')
    return redirect(url_for('main.admin_dashboard'))


@main.route('/admin/api/get_all_latest_locations')
@login_required
@admin_required
def get_all_latest_locations(): return jsonify(get_all_users_latest_location())
@main.route('/api/get_geofences')
@login_required
def get_geofences_api_user(): return jsonify(get_geofences())
@main.route('/admin/get_location_history/<user_page_id>')
@login_required
@admin_required
def get_location_history(user_page_id): return jsonify(get_user_location_history(user_page_id))
@main.route('/admin/export_logs/<user_page_id>/<username>/<export_format>')
@login_required
@admin_required
def export_logs(user_page_id, username, export_format):
    logs = get_user_logs_for_export(user_page_id)
    if not logs:
        flash(f"No logs found for user {username} to export.", "info")
        return redirect(url_for('main.admin_dashboard'))
    filename = f"{username}_location_history.{export_format}"
    if export_format == 'csv':
        output = io.StringIO(); writer = csv.DictWriter(output, fieldnames=logs[0].keys()); writer.writeheader(); writer.writerows(logs)
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-disposition": f"attachment; filename={filename}"})
    elif export_format == 'html':
        return Response(render_template('export_template.html', logs=logs, username=username), mimetype="text/html", headers={"Content-disposition": f"attachment; filename={filename}"})
    elif export_format == 'pdf':
        pdf = PDF(orientation='L', unit='mm', format='A4'); pdf.add_page(); pdf.set_font("Helvetica", size=8); header = list(logs[0].keys()); col_widths = {'Timestamp': 45, 'Latitude': 20, 'Longitude': 20, 'IPAddress': 25, 'Battery': 40, 'DeviceInfo': 120}; pdf.set_fill_color(200, 220, 255)
        for col_name in header: pdf.cell(col_widths.get(col_name, 30), 7, col_name, 1, 0, 'C', 1)
        pdf.ln(); pdf.set_fill_color(255, 255, 255)
        for row in logs:
            for col_name in header: pdf.cell(col_widths.get(col_name, 30), 6, str(row.get(col_name, '')), 1)
            pdf.ln()
        pdf_buffer = io.BytesIO(pdf.output()); pdf_buffer.seek(0)
        return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
    flash(f"Invalid export format: {export_format}", "danger")
    return redirect(url_for('main.admin_dashboard'))

@main.route('/api/get_active_users_count')
@login_required
def get_active_users_count():
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': 'Forbidden'}), 403

    users = get_all_users()
    return jsonify({'count': len(users)})

@main.route('/api/get_geofence_count')
@login_required
def get_geofence_count():
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': 'Forbidden'}), 403

    geofences = get_geofences()
    return jsonify({'count': len(geofences)})