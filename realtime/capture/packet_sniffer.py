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
            from scapy.all import conf
            default_iface = conf.iface
            print(f"[*] Automatically binding to default interface: {default_iface}")
            
            sniff(
                prn=self.packet_callback,
                store=False,
                iface=default_iface,
                stop_filter=lambda p: not self.running
            )
        except (PermissionError, OSError):
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
        import logging
        logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
        from scapy.all import IP, TCP, Ether, Raw

        client_ports = [1024, 1025, 1026, 1027, 1028]
        dst_ips = ["192.168.1.1", "192.168.1.20", "192.168.1.50"]

        while self.running:
            sport = random.choice(client_ports)
            dst_ip = random.choice(dst_ips)
            payload_len = random.randint(0, 1200)
            payload = Raw(b"X" * payload_len) if payload_len > 0 else b""
            
            # Create a mock TCP packet with realistic features to simulate traffic
            pkt = Ether() / IP(src="192.168.1.100", dst=dst_ip) / TCP(sport=sport, dport=80) / payload
            pkt.time = time.time()
            
            self.packet_callback(pkt)
            
            time.sleep(random.uniform(0.02, 0.08))

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

    # ==========================================
    # STOP
    # ==========================================

    def stop(self):

        self.running = False
