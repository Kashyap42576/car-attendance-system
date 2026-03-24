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

sheet = client.open("Vehicle Scan Logs").sheet1 
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

    new_row = [current_time, driver_id, car_id, lat, lng]

    try:
        sheet.append_row(new_row)
        print(f"Logged to Sheets: Driver {driver_id} in Car {car_id}")
        return jsonify({"status": "success", "message": "Attendance marked in Google Sheets!"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": "Failed to sync with Google Sheets."}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
