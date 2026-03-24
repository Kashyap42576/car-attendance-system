from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", 
         "https://www.googleapis.com/auth/drive"]

# Authenticate using your downloaded JSON key
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the main spreadsheet
spreadsheet = client.open("Vehicle Scan Logs")

# Connect to the specific tabs (Make sure these exact names match your Google Sheet!)
log_sheet = spreadsheet.worksheet("Logs")
cred_sheet = spreadsheet.worksheet("Credentials")
# ---------------------------

# 1. Route for the Main Scanner App
@app.route('/')
def index():
    return render_template('index.html')

# 2. Route to Handle the Data from the Phone
@app.route('/log_scan', methods=['POST'])
def log_scan():
    data = request.json
    driver_id = data.get('driver_id')
    car_id = data.get('car_id')
    lat = data.get('lat')
    lng = data.get('lng')
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # SECURITY CHECK: Get all allowed IDs from Column A of the Credentials tab
        allowed_drivers = cred_sheet.col_values(1)

        # If the driver ID is NOT in the list, reject the scan
        if driver_id not in allowed_drivers:
            print(f"Rejected: Unauthorized ID attempted ({driver_id})")
            return jsonify({"status": "error", "message": f"Driver ID '{driver_id}' not found. Access Denied."})

        # If the driver is approved, log the data
        new_row = [current_time, driver_id, car_id, lat, lng]
        log_sheet.append_row(new_row)
        
        print(f"Logged to Sheets: Driver {driver_id} in Car {car_id}")
        return jsonify({"status": "success", "message": "Attendance marked successfully!"})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": "Failed to sync with the server."})

# 3. Route for the Admin Dashboard
@app.route('/admin')
def admin_dashboard():
    try:
        # Fetch all rows from the Logs tab
        all_records = log_sheet.get_all_values()
        
        # If the sheet is completely empty, handle it gracefully
        if not all_records:
            return render_template('admin.html', headers=[], data=[])
            
        # The first row contains the headers (Timestamp, Driver ID, etc.)
        headers = all_records[0]
        # Everything from the second row onwards is the actual scan data
        data = all_records[1:]
        
        # Reverse the data so the newest scans appear at the top!
        data.reverse()

        return render_template('admin.html', headers=headers, data=data)
        
    except Exception as e:
        print(f"Dashboard Error: {e}")
        return f"<h3>Error loading dashboard. Check the server terminal for details.</h3>"

if __name__ == '__main__':
    # host='0.0.0.0' allows mobile devices on the same network to connect
    app.run(debug=True, host='0.0.0.0', port=5000)
