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
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    with open(DATA_FILE, "w") as f:
        json.dump(history, f, indent=4)

def calculate_period_simple():
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    total_minutes = utc_now.hour * 60 + utc_now.minute
    date_str = utc_now.strftime("%Y%m%d")
    period_suffix = 10001 + total_minutes
    return date_str + "1000" + str(period_suffix)

def get_real_result_map():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
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
    except:
        return {}

def background_predictor():
    print("API is LIVE and Syncing...")
    while True:
        try:
            history = load_history()
            current_period = calculate_period_simple()
            
            # Check for current period
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

            # Update all PENDING or missing results
            real_data = get_real_result_map()
            if real_data:
                updated = False
                for entry in history:
                    p_no = entry.get("period no")
                    if entry.get("result", "PENDING") == "PENDING" and p_no in real_data:
                        actual = real_data[p_no]
                        entry["result"] = "WIN" if entry["prediction"] == actual else "LOSS"
                        updated = True
                
                if updated:
                    save_history(history[-100:])
            else:
                # Save new entries even if real_data is empty
                save_history(history[-100:])

        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(15) 

# --- RENDER PAR CHALANE KE LIYE YE ZARURI HAI ---
# Threading ko if __name__ == '__main__': se bahar rakha hai
t = threading.Thread(target=background_predictor)
t.daemon = True
t.start()

@app.route('/')
def home():
    return "API is Running! Go to /predict"

@app.route('/predict', methods=['GET'])
def get_prediction():
    return jsonify(load_history()[::-1])

if __name__ == '__main__':
    # Render hamesha PORT environment variable provide karta hai
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
