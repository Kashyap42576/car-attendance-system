from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "super_secret_workshop_key" # Secure the session

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

# --- 1. NEW DRIVER LOGIN SYSTEM ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        entered_id = request.form.get('driver_id')
        
        # Pull ALL credentials (rows) from the Credentials sheet
        all_credentials = cred_sheet.get_all_records()
        
        # Check if the ID exists and find the name
        driver_found = False
        driver_name = ""
        for row in all_credentials:
            if str(row['Driver ID']) == entered_id:
                driver_found = True
                driver_name = row['Driver Name']
                break

        if driver_found:
            # Successfully logged in: store both ID and Name in the session!
            session['driver_id'] = entered_id
            session['driver_name'] = driver_name
            return redirect(url_for('scanner'))
        else:
            return render_template('driver_login.html', error="Invalid ID. Access Denied.")
            
    return render_template('driver_login.html')

# --- 2. UPDATED SCANNER ROUTE ---
@app.route('/')
def scanner():
    # Security checkpoint
    if 'driver_id' not in session or 'driver_name' not in session:
        return redirect(url_for('login'))
        
    # Pass BOTH dynamic pieces of data to the design
    return render_template('index.html', driver_id=session['driver_id'], driver_name=session['driver_name'])

# --- 3. HANDLE THE SCAN DATA ---
@app.route('/log_scan', methods=['POST'])
def log_scan():
    if 'driver_id' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.json
    driver_id = session['driver_id'] # Use the logged-in ID
    car_id = data.get('car_id')
    lat = data.get('lat')
    lng = data.get('lng')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        new_row = [current_time, driver_id, car_id, lat, lng]
        log_sheet.append_row(new_row)
        print(f"Logged: {driver_id} scanned {car_id}")
        return jsonify({"status": "success", "message": "Attendance marked!"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to sync."}), 500

# --- 4. ADMIN DASHBOARD & LOGIN ---
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

@app.route('/admin')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    try:
        all_records = log_sheet.get_all_values()
        if not all_records: return render_template('admin.html', headers=[], data=[])
        headers = all_records[0]
        data = all_records[1:]; data.reverse()
        return render_template('admin.html', headers=headers, data=data)
    except Exception as e: return f"<h3>Error loading dashboard.</h3>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
