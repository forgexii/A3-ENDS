#!/usr/bin/env python3
"""
==============================================================================
A3-ENDS: Standalone Attack Sample Injection Utility
==============================================================================

Purpose:
  Simulate targeted cyber attack vectors by injecting physical-flow feature
  samples from the CICIDS2017 benchmark dataset into the running A3-ENDS
  FastAPI orchestration backend.

IMPORTANT ARCHITECTURAL NOTE:
  This script is a standalone on-demand testing tool. It is intentionally
  NOT included in the automatic system startup (start_all.sh).
  Run this tool independently in a separate terminal when you wish to test
  model inference, SHAP explanations, HITL popups, and adaptive responses.

Usage:
  python generate_attack_samples.py --help
  python generate_attack_samples.py --list
  python generate_attack_samples.py --attack DoS
  python generate_attack_samples.py --attack all --delay 2.0
  python generate_attack_samples.py --interactive
==============================================================================
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import requests

DEFAULT_API_URL = "http://127.0.0.1:8000/api/detection/process"
DEFAULT_HEALTH_URL = "http://127.0.0.1:8000/api/health"


class AttackSampleGenerator:
    """Manages loading of test data and firing attack payloads into A3-ENDS."""

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path(__file__).resolve().parent / "datasets/realtime_features/CICIDS2017"

        self.data_dir = data_dir
        self.X_test: Optional[np.ndarray] = None
        self.y_test: Optional[np.ndarray] = None
        self.scaler = None
        self.mapping: Dict[str, str] = {}
        self._loaded = False

    def check_backend_health(self, health_url: str = DEFAULT_HEALTH_URL) -> bool:
        """Verify that the A3-ENDS FastAPI backend is reachable."""
        try:
            resp = requests.get(health_url, timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def load_dataset(self):
        """Load the scaled test set, scaler, and class mappings."""
        if self._loaded:
            return

        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"Dataset directory not found: {self.data_dir}\n"
                f"Please ensure datasets/realtime_features/CICIDS2017 is present."
            )

        self.X_test = np.load(self.data_dir / "X_test.npy")
        self.y_test = np.load(self.data_dir / "y_test.npy")
        self.scaler = joblib.load(self.data_dir / "scaler.pkl")

        with open(self.data_dir / "label_mapping.json", "r") as f:
            self.mapping = json.load(f)

        self._loaded = True

    def list_attack_types(self) -> Dict[str, int]:
        """Return all available non-benign attack classes and sample counts."""
        self.load_dataset()
        counts = {}
        for class_id_str, label_name in self.mapping.items():
            cid = int(class_id_str)
            if cid == 0 or label_name.lower() == "benign":
                continue
            indices = np.where(self.y_test == cid)[0]
            counts[label_name] = len(indices)
        return counts

    def get_sample_for_class(self, label_name: str) -> Optional[Dict]:
        """Extract a single unscaled physical-feature flow record for a class."""
        self.load_dataset()

        # Resolve class ID
        target_cid = None
        target_label = None
        for class_id_str, name in self.mapping.items():
            if name.lower().replace(" ", "").replace("_", "") == label_name.lower().replace(" ", "").replace("_", ""):
                target_cid = int(class_id_str)
                target_label = name
                break

        if target_cid is None:
            return None

        indices = np.where(self.y_test == target_cid)[0]
        if len(indices) == 0:
            return None

        chosen_idx = random.choice(indices)
        scaled_row = self.X_test[chosen_idx:chosen_idx + 1]
        phys_row = self.scaler.inverse_transform(scaled_row)[0]

        features = {
            "source_ip": f"192.168.1.{random.randint(10, 250)}",
            "destination_ip": "192.168.56.1",
            "source_port": random.randint(1024, 65535),
            "destination_port": 80 if "web" in target_label.lower() or "dos" in target_label.lower() else 22,
            "protocol": 6,
            "duration": float(max(0.0, phys_row[0])),
            "packet_count": int(max(1, round(phys_row[1]))),
            "mean_packet_size": float(max(0.0, phys_row[2])),
            "std_packet_size": float(max(0.0, phys_row[3])),
            "total_bytes": float(max(0.0, phys_row[4])),
            "mean_iat": float(max(0.0, phys_row[5])),
        }
        return {"class_name": target_label, "features": features}

    def fire_attack(self, class_name: str, features: Dict, target_url: str = DEFAULT_API_URL) -> bool:
        """Transmit the feature payload to the backend API."""
        print(f"\n[*] INJECTING ATTACK: '{class_name}' -> {target_url}")
        print(f"    Flow Source: {features['source_ip']}:{features['source_port']} -> {features['destination_ip']}:{features['destination_port']}")
        print(f"    Features   : {features['packet_count']} pkts | {features['duration']:.1f} µs | {features['total_bytes']:.1f} B/s")

        try:
            t0 = time.time()
            resp = requests.post(target_url, json=features, timeout=10)
            elapsed_ms = (time.time() - t0) * 1000

            if resp.status_code == 200:
                data = resp.json()
                print(f"    [✓] API Response (status 200 OK, latency: {elapsed_ms:.1f}ms):")
                print(f"        Pipeline ID : {data.get('pipeline_id')}")
                print(f"        Attack Type : {data.get('attack_type')} (Confidence: {data.get('confidence', 0) * 100:.1f}%)")
                print(f"        Severity    : {data.get('severity')} (Risk Score: {data.get('risk_score')})")
                print(f"        Anomaly     : {data.get('anomaly_detected')} (Score: {data.get('anomaly_score', 0):.6f})")

                # Print top SHAP features if present
                shap = data.get("shap_explanation")
                if isinstance(shap, dict):
                    top_feats = sorted(shap.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
                    shap_str = ", ".join(f"{k}: {v:+.2f}" for k, v in top_feats)
                    print(f"        Top SHAP    : {shap_str}")

                hitl = data.get("analyst_approval", {})
                if hitl.get("requires_analyst"):
                    print(f"        HITL Action : {hitl.get('action')} (Waiting for SOC analyst approval)")
                return True
            else:
                print(f"    [!] Backend returned error {resp.status_code}: {resp.text}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"    [!] Connection Refused: Backend API is offline at {target_url}.")
            print(f"        Start the system first with: ./start_all.sh")
            return False
        except Exception as exc:
            print(f"    [!] Request failed: {exc}")
            return False


def interactive_menu(generator: AttackSampleGenerator, target_url: str):
    """Interactive CLI menu for SOC analysts."""
    attack_types = generator.list_attack_types()
    names = list(attack_types.keys())

    while True:
        print("\n" + "=" * 60)
        print("  A3-ENDS Interactive Attack Injection Menu")
        print("=" * 60)
        for idx, name in enumerate(names, start=1):
            print(f"  [{idx}] {name} ({attack_types[name]} benchmark samples)")
        print(f"  [{len(names) + 1}] Inject ALL Attack Types Sequentially")
        print(f"  [0] Exit")
        print("=" * 60)

        choice = input("Select an option (0-8): ").strip()
        if choice == "0":
            print("Exiting.")
            break
        elif choice == str(len(names) + 1):
            for name in names:
                sample = generator.get_sample_for_class(name)
                if sample:
                    generator.fire_attack(sample["class_name"], sample["features"], target_url)
                    time.sleep(1.5)
        elif choice.isdigit() and 1 <= int(choice) <= len(names):
            selected_name = names[int(choice) - 1]
            sample = generator.get_sample_for_class(selected_name)
            if sample:
                generator.fire_attack(sample["class_name"], sample["features"], target_url)
        else:
            print("[!] Invalid selection, please try again.")


def main():
    parser = argparse.ArgumentParser(
        description="A3-ENDS Standalone Cyber Attack Sample Injection Tool",
        epilog="Note: This tool is strictly standalone and is NOT run by start_all.sh."
    )
    parser.add_argument(
        "-a", "--attack",
        type=str,
        help="Specific attack class to inject (e.g. DoS, DDoS, Botnet, Portscan, Web Attack, Infiltration, Brute Force, or 'all')"
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List all available attack types and their sample counts in the dataset"
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=1,
        help="Number of samples to fire per attack type (default: 1)"
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=1.0,
        help="Delay in seconds between consecutive injections (default: 1.0s)"
    )
    parser.add_argument(
        "-t", "--target",
        type=str,
        default=DEFAULT_API_URL,
        help=f"Target detection API endpoint (default: {DEFAULT_API_URL})"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive menu selection mode"
    )

    args = parser.parse_args()

    generator = AttackSampleGenerator()

    # Handle --list
    if args.list:
        print("\nAvailable Attack Types in CICIDS2017 Benchmark Dataset:")
        print("-" * 55)
        for name, count in generator.list_attack_types().items():
            print(f"  • {name:<20} : {count:>8} test samples")
        print("-" * 55)
        print("To inject an attack, run:")
        print("  python generate_attack_samples.py --attack DoS\n")
        return

    # Check backend reachability before proceeding
    if not generator.check_backend_health():
        print(f"\n[!] WARNING: A3-ENDS Backend is offline at {DEFAULT_HEALTH_URL}.")
        print("    Please start the system first using:")
        print("      ./start_all.sh")
        print("    or in a separate terminal:")
        print("      ./start_all.sh --backend\n")
        sys.exit(1)

    # Handle --interactive or no arguments
    if args.interactive or (not args.attack and not args.list):
        interactive_menu(generator, args.target)
        return

    # Handle targeted attack injection
    attack_name = args.attack.strip()
    available_attacks = list(generator.list_attack_types().keys())

    if attack_name.lower() == "all":
        targets = available_attacks
    else:
        # Match case-insensitively
        matched = [a for a in available_attacks if a.lower().replace(" ", "") == attack_name.lower().replace(" ", "")]
        if not matched:
            print(f"[!] Unknown attack '{attack_name}'. Available: {', '.join(available_attacks)}")
            return
        targets = matched

    print(f"\n[*] Firing {args.count} sample(s) for target(s): {', '.join(targets)}")
    for t in targets:
        for i in range(args.count):
            sample = generator.get_sample_for_class(t)
            if sample:
                generator.fire_attack(sample["class_name"], sample["features"], args.target)
                if args.delay > 0:
                    time.sleep(args.delay)


if __name__ == "__main__":
    main()
