import pandas as pd
import requests
import time
import json
import random

def load_samples():
    print("Loading CICIDS2017 dataset (this may take a minute)...")
            
    df = pd.read_csv("datasets/cleaned_cicids2017/cleaned_cicids2017.csv")
    
    samples = {}
    
    # We will pick exactly 1 row for each attack type found in the dataset
    for label in df['Label'].unique():
        if label != "BENIGN":
            # Get one random row for this attack
            row = df[df['Label'] == label].sample(1).iloc[0]
            
            # Map CICIDS2017 features to our API features
            features = {
                "source_ip": f"192.168.1.{random.randint(10, 250)}",
                "destination_ip": "192.168.56.1",
                "source_port": random.randint(1024, 65535),
                "destination_port": 80,
                "protocol": 6,
                
                "duration": float(row["Flow Duration"]),
                "packet_count": int(row["Total Fwd Packets"] + row.get("Total Backward Packets", 0)),
                "mean_packet_size": float(row["Fwd Packet Length Mean"]),
                "std_packet_size": float(row["Fwd Packet Length Std"]),
                "total_bytes": float(row["Flow Bytes/s"]),
                "mean_iat": float(row["Flow IAT Mean"])
            }
            samples[label] = features
            
    return samples

def fire_attack(name, features):
    print(f"\n[*] Firing '{name}' into A3-ENDS API...")
    try:
        response = requests.post("http://127.0.0.1:8000/api/detection/process", json=features)
        if response.status_code == 200:
            res = response.json()
            print(f"    -> Success! Detected as: {res.get('attack_type')} (Severity: {res.get('severity')})")
        else:
            print(f"    -> API Error: {response.text}")
    except Exception as e:
        print(f"    -> Connection failed: {e}")

if __name__ == "__main__":
    samples = load_samples()
    print("\n--- SAMPLES LOADED ---")
    
    for name, features in samples.items():
        fire_attack(name, features)
        time.sleep(1) # wait for UI to update
