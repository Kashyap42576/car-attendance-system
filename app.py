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

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the main spreadsheet
spreadsheet = client.open("Vehicle Scan Logs")

# Connect to the specific tabs
log_sheet = spreadsheet.worksheet("Logs")
cred_sheet = spreadsheet.worksheet("Credentials")
# ---------------------------

@app.route('/')
def index():
    return render_template('index.html')

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
        # (This pulls a list of everything in the first column)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
