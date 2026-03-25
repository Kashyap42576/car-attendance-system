from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import zoneinfo
import os

app = Flask(__name__)
app.secret_key = "super_secret_workshop_key" 

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", 
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Vehicle Scan Logs")
log_sheet = spreadsheet.worksheet("Logs")
cred_sheet = spreadsheet.worksheet("Credentials")
# ---------------------------

# --- 1. STAFF LOGIN SYSTEM ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entered_id = request.form.get('staff_id')
        
        # Pull all raw values to avoid header mismatch errors
        all_credentials = cred_sheet.get_all_values()
        
        staff_found = False
        staff_name = ""
        
        # Loop through rows. row[0] is Col A (ID), row[1] is Col B (Name)
        for row in all_credentials:
            if len(row) >= 2 and str(row[0]).strip() == entered_id.strip():
                staff_found = True
                staff_name = row[1]
                break

        if staff_found:
            session['staff_id'] = entered_id
            session['staff_name'] = staff_name
            return redirect(url_for('scanner'))
        else:
            return render_template('login.html', error="Invalid Staff ID. Access Denied.")
            
    return render_template('login.html')

# --- 2. THE SCANNER PAGE ---
@app.route('/')
def scanner():
    if 'staff_id' not in session or 'staff_name' not in session:
        return redirect(url_for('login')) 
        
    return render_template('index.html', staff_id=session['staff_id'], staff_name=session['staff_name'])

# --- 3. HANDLE THE SCAN DATA ---
@app.route('/log_scan', methods=['POST'])
def log_scan():
    if 'staff_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.json
    staff_id = session['staff_id'] 
    qr_id = data.get('qr_id')
    lat = data.get('lat')
    lng = data.get('lng')
    
    ist = zoneinfo.ZoneInfo('Asia/Kolkata')
    current_time = datetime.now(ist).strftime("%d-%m-%Y %I:%M:%S %p")

    try:
        new_row = [current_time, staff_id, qr_id, lat, lng]
        log_sheet.append_row(new_row)
        print(f"Logged: {staff_name} scanned {qr_id} at {current_time}")
        return jsonify({"status": "success", "message": "Attendance marked!"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to sync."}), 500

# --- 4. ADMIN LOGIN SYSTEM ---
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        entered_pin = request.form.get('pin')
        
        if entered_pin == "1234":
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Incorrect PIN.")
            
    return render_template('admin_login.html')

# --- 5. THE ADMIN DASHBOARD ---
@app.route('/admin')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))

    try:
        all_records = log_sheet.get_all_values()
        if not all_records:
            return render_template('admin.html', headers=[], data=[])
            
        headers = all_records[0]
        data = all_records[1:]
        data.reverse() 
        return render_template('admin.html', headers=headers, data=data)
    except Exception as e:
        return f"<h3>Error loading dashboard.</h3>"

# --- 6. LOGOUT ROUTE ---
@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
