import threading

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


sniffer = PacketSniffer()

flow_manager = FlowManager()

extractor = FeatureExtractor()

engine = InferenceEngine()


threading.Thread(

    target=sniffer.start,

    daemon=True

).start()


while True:

    packet = sniffer.get_packet()

    if packet is None:

        continue

    flow_manager.add_packet(
        packet
    )

    completed = (
        flow_manager.expire_flows()
    )

    for flow in completed:

        features = (
            extractor.extract(
                flow
            )
        )

        result = (
            engine.detect(
                features
            )
        )

        print("\nFLOW")

        print(features)

        print("\nRESULT")

        print(result)