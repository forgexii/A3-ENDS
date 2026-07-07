import requests
import time

def trigger_popup():
    print("Sending a massive ZERO_DAY_ANOMALY payload to force a HIGH severity alert...")
    
    # This payload is mathematically guaranteed to shatter the Autoencoder threshold
    features = {
        "source_ip": "6.6.6.6",
        "destination_ip": "192.168.56.1",
        "source_port": 12345,
        "destination_port": 80,
        "protocol": 6,
        "duration": 500.0,
        "packet_count": 999999,
        "mean_packet_size": 54.0,
        "std_packet_size": 0.0,
        "total_bytes": 9999999.0,
        "mean_iat": 0.0001
    }

    try:
        response = requests.post("http://127.0.0.1:8000/api/detection/process", json=features)
        if response.status_code == 200:
            res = response.json()
            print(f"-> Success! API classified as: {res.get('attack_type')} (Severity: {res.get('severity')})")
            print("-> Check your Desktop UI! The 5-second HITL Pop-up should be on your screen.")
        else:
            print(f"-> API Error: {response.text}")
    except Exception as e:
        print(f"-> Connection failed: {e}. Is your FastAPI server running?")

if __name__ == "__main__":
    trigger_popup()
