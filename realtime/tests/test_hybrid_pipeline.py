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


sniffer = PacketSniffer()

flow_manager = FlowManager()

extractor = FeatureExtractor()

engine = InferenceEngine()

event_store = EventStore()


capture_thread = threading.Thread(

    target=sniffer.start,

    daemon=True

)

capture_thread.start()

print(
    "\nRealtime Hybrid Pipeline Started...\n"
)


while True:

    packet = sniffer.get_packet()

    if packet is None:

        time.sleep(0.01)

        continue

    flow_manager.add_packet(
        packet
    )

    completed_flows = (
        flow_manager.expire_flows()
    )

    for flow in completed_flows:

        try:

            features = extractor.extract(
                flow
            )

            result = engine.detect(
                features
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

                "confidence":
                    result.get(
                        "confidence"
                    ),

                "attack_type":
                    result.get(
                        "attack_type"
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

            print("SAVING EVENT")
            print(event)

            event_store.add_event(
                event
            )

            print(
                "\nDetection stored."
            )

            print(
                "\n===================="
            )

            print(
                "FLOW FEATURES"
            )

            print(
                "===================="
            )

            print(
                features
            )

            print(
                "\n===================="
            )

            print(
                "DETECTION RESULT"
            )

            print(
                "===================="
            )

            print(
                result
            )

        except Exception as e:

            print(
                "\nPIPELINE ERROR:"
            )

            print(
                str(e)
            )