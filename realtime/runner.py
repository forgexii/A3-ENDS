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

from realtime.inference.inference_engine import (
    InferenceEngine
)

from backend.services.event_store import (
    EventStore
)


class RealtimeEngine:

    def __init__(self):

        self.sniffer = PacketSniffer()

        self.flow_manager = FlowManager()

        self.extractor = FeatureExtractor()

        self.inference_engine = (
            InferenceEngine()
        )

        self.event_store = EventStore()

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

        result = (

            self.inference_engine.detect(
                features
            )

        )

        event = {

            "source_ip":
                features[
                    "source_ip"
                ],

            "destination_ip":
                features[
                    "destination_ip"
                ],

            "source_port":
                features[
                    "source_port"
                ],

            "destination_port":
                features[
                    "destination_port"
                ],

            "protocol":
                features[
                    "protocol"
                ],

            "anomaly_score":
                result[
                    "anomaly_score"
                ],

            "threshold":
                result[
                    "threshold"
                ],

            "is_anomaly":
                result[
                    "is_anomaly"
                ],

            "classification":
                result.get(
                    "classification"
                ),

            "attack_type":
                result.get(
                    "attack_type"
                ),

            "confidence":
                result.get(
                    "confidence"
                ),

            "severity":
                result.get(
                    "severity"
                ),

            "risk_score":
                result.get(
                    "risk_score"
                )
        }

        self.event_store.add_event(
            event
        )

        print(
            "\nDetection Stored"
        )

        print(
            f"Anomaly: "
            f"{event['is_anomaly']}"
        )

        print(
            f"Score: "
            f"{event['anomaly_score']}"
        )

    # ==========================================
    # STOP
    # ==========================================

    def stop(self):

        self.running = False

        self.event_store.close()


if __name__ == "__main__":

    RealtimeEngine().start()