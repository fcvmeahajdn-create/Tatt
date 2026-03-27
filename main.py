import json
import os
import datetime
import random
import time
import threading
import requests
from flask import Flask, jsonify

app = Flask(__name__)
# JSON ko browser me "Pretty" (saaf) dikhane ke liye
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
DATA_FILE = "history.json"
REAL_API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json"

def load_history():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(DATA_FILE, "w") as f:
        json.dump(history, f, indent=4)

def calculate_period_simple():
    # Get current UTC time
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    
    # Calculate total minutes since midnight
    total_minutes = utc_now.hour * 60 + utc_now.minute
    
    # Format date as yyyyMMdd
    date_str = utc_now.strftime("%Y%m%d")
    
    # Format suffix
    period_suffix = 10001 + total_minutes
    
    # Combine everything
    return date_str + "1000" + str(period_suffix)

def get_real_result_map():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(REAL_API_URL, headers=headers, timeout=10)
        data = response.json()
        results_map = {}
        game_list = data.get('data', {}).get('list', [])
        for item in game_list:
            issue = str(item.get('issueNumber'))
            num_val = item.get('number')
            if num_val is not None:
                results_map[issue] = "BIG" if int(num_val) >= 5 else "SMALL"
        return results_map
    except Exception as e:
        print(f"Fetch Error: {e}")
        return {}

def background_predictor():
    print("Background Sync Started...")
    while True:
        try:
            history = load_history()
            current_period = calculate_period_simple()
            
            # 1. Check if current period already exists
            if not any(entry.get("period no") == current_period for entry in history):
                random.seed(current_period)
                pred = random.choice(["BIG", "SMALL"])
                random.seed()
                
                new_entry = {
                    "period no": current_period,
                    "prediction": pred,
                    "result": "PENDING",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                history.append(new_entry)

            # 2. Sync PENDING results with Real API
            real_data = get_real_result_map()
            if real_data:
                updated = False
                for entry in history:
                    p_no = entry.get("period no")
                    if entry.get("result") == "PENDING" and p_no in real_data:
                        actual = real_data[p_no]
                        entry["result"] = "WIN" if entry["prediction"] == actual else "LOSS"
                        updated = True
                
                if updated:
                    # Save only if something changed
                    pass

            # Max 100 records and save
            save_history(history[-100:])

        except Exception as e:
            print(f"Background Error: {e}")
            
        time.sleep(20) # Sync every 20 seconds

@app.route('/')
def home():
    return "API is Running! Go to /predict to see results."

@app.route('/predict', methods=['GET'])
def get_prediction():
    return jsonify(load_history()[::-1])

if __name__ == '__main__':
    # Start background thread
    t = threading.Thread(target=background_predictor)
    t.daemon = True
    t.start()
    
    # RAILWAY PORT CONFIGURATION
    # Railway hamesha PORT variable deta hai, agar nahi mile toh default 5000
    port = int(os.environ.get("PORT", 5000))Sun phir toh niche 


# --- CHANGE 1: Thread ko if block se bahar nikala ---
t = threading.Thread(target=background_predictor)
t.daemon = True
t.start()

@app.route('/')
def home():
    return "API is Running! Go to /predict"

@app.route('/predict', methods=['GET'])
def get_prediction():
    return jsonify(load_history()[::-1])

# --- CHANGE 2: Port fix for Render ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


Ye lagane pr he ho jayega ??
    app.run(host='0.0.0.0', port=port)
