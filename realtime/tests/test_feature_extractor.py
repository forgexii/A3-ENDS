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


sniffer = PacketSniffer()

flow_manager = FlowManager()

extractor = FeatureExtractor()


threading.Thread(

    target=sniffer.start,

    daemon=True

).start()


print(
    "Waiting for flows..."
)


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

        print("\nFEATURES")

        print(features)