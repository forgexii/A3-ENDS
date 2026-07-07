"""
Realtime AI-NIDS Runner

Production runtime for:

Packet Capture
    ->
Flow Aggregation
    ->
Feature Extraction
    ->
Autoencoder Detection
    ->
Classification
    ->
Risk Assessment
    ->
Response Engine
    ->
Database Storage
"""

import threading
import time

from realtime.capture.packet_sniffer import (
    PacketSniffer
)

from realtime.flows.flow_manager import (
    FlowManager
)

from realtime.features.feature_extractor import (
    FeatureExtractor
)

import requests


class RealtimeEngine:

    def __init__(self):

        self.sniffer = PacketSniffer()

        self.flow_manager = FlowManager()

        self.extractor = FeatureExtractor()

        self.running = False

    # ==========================================
    # START
    # ==========================================

    def start(self):

        self.running = True

        capture_thread = threading.Thread(

            target=self.sniffer.start,

            daemon=True

        )

        capture_thread.start()

        print(
            "\nRealtime AI-NIDS Started\n"
        )

        while self.running:

            try:

                packet = (
                    self.sniffer.get_packet()
                )

                if packet is None:

                    time.sleep(
                        0.01
                    )

                    continue

                self.flow_manager.add_packet(
                    packet
                )

                completed_flows = (

                    self.flow_manager
                    .expire_flows()

                )

                for flow in completed_flows:

                    self.process_flow(
                        flow
                    )

            except Exception as e:

                print(
                    "\nENGINE ERROR:"
                )

                print(str(e))

    # ==========================================
    # PROCESS FLOW
    # ==========================================

    def process_flow(

        self,
        flow

    ):

        features = (
            self.extractor.extract(
                flow
            )
        )
        
        print(f"\n[DEBUG] Extracted Features: {features['packet_count']} pkts, {features['duration']} duration")

        try:
            # Forward the features to the main A3-ENDS Orchestration API
            response = requests.post(
                "http://127.0.0.1:8000/api/detection/process", 
                json=features,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                print("\nDetection Processed by API")
                print(f"Anomaly: {result.get('status') == 'anomaly_detected'}")
                print(f"Score: {result.get('steps', {}).get('autoencoder', {}).get('score', 0)}")
            else:
                print(f"\nAPI Error: {response.text}")
                
        except Exception as e:
            print(f"\nFailed to reach backend API: {e}")

    # ==========================================
    # STOP
    # ==========================================

    def stop(self):

        self.running = False


if __name__ == "__main__":

    RealtimeEngine().start()