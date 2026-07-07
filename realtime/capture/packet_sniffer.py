"""
Packet Sniffer

Captures live packets from the network
and forwards them to the processing
pipeline.
"""

from queue import Queue

from scapy.all import sniff


class PacketSniffer:

    def __init__(self):

        self.packet_queue = Queue()

        self.running = False

    # ==========================================
    # PACKET CALLBACK
    # ==========================================

    def packet_callback(self, packet):

        self.packet_queue.put(
            packet
        )

        print(
            f"[CAPTURED] "
            f"{packet.summary()}"
        )

    # ==========================================
    # START CAPTURE
    # ==========================================

    def start(self):

        self.running = True

        print(
            "Starting packet capture..."
        )

        try:
            sniff(
                prn=self.packet_callback,
                store=False,
                iface="vboxnet0"
            )
        except PermissionError:
            print(
                "\n[WARNING] Root privileges required for raw packet sniffing."
            )
            print(
                "Falling back to simulated packet generation for development..."
            )
            self._start_simulation()

    # ==========================================
    # SIMULATE PACKETS
    # ==========================================

    def _start_simulation(self):
        
        import time
        import random
        from scapy.all import IP, TCP, Ether

        while self.running:
            
            # Create a mock TCP packet with randomized ports/sizes to simulate traffic
            pkt = Ether() / IP(src="192.168.1.100", dst="10.0.0.5") / TCP(sport=random.randint(1024, 65535), dport=80)
            
            self.packet_callback(pkt)
            
            time.sleep(random.uniform(0.01, 0.1))

    # ==========================================
    # GET NEXT PACKET
    # ==========================================

    def get_packet(self):

        if self.packet_queue.empty():

            return None

        return self.packet_queue.get()

    # ==========================================
    # QUEUE SIZE
    # ==========================================

    def queue_size(self):

        return self.packet_queue.qsize()