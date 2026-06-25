from realtime.capture.packet_sniffer import (
    PacketSniffer
)

from realtime.flows.flow_manager import (
    FlowManager
)
import threading

sniffer = PacketSniffer()

flow_manager = FlowManager()


def process_packets():

    while True:

        packet = sniffer.get_packet()

        if packet is None:

            continue

        flow_manager.add_packet(
            packet
        )

        flows = (
            flow_manager.expire_flows()
        )

        for flow in flows:

            print(
                "\nFLOW COMPLETED"
            )

            print(
                f"Packets: "
                f"{len(flow['packets'])}"
            )

threading.Thread(
    target=sniffer.start,
    daemon=True
).start()

process_packets()