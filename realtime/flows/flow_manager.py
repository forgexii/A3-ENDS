"""
Flow Manager

Groups packets into bidirectional
network flows.

Includes port scan aggregation:
When a single source IP sends SYN probes to many different destination ports
(typical Nmap scan), individual per-port flows are tiny (1-2 pkts, 0 duration)
and invisible to the Autoencoder. The port scan tracker aggregates these into
a single "meta-flow" with realistic feature values so the ML pipeline can
detect the scan.
"""

import time

from collections import defaultdict


class FlowManager:

    def __init__(self):

        self.flow_timeout = 5
        self.active_timeout = 2  # Process ongoing flows every 2 seconds for real-time detection

        self.flows = defaultdict(
            lambda: {
                "first_seen": None,
                "last_seen": None,
                "packets": [],
                "flow_key": None
            }
        )

        # ── Port Scan Tracker ─────────────────────
        # Tracks unique destination ports per source IP within a time window
        self.scan_tracker = defaultdict(
            lambda: {
                "first_seen": None,
                "last_seen": None,
                "dest_ports": set(),
                "packets": [],
                "dest_ip": None,
            }
        )
        self.scan_window = 10       # seconds to aggregate scan probes
        self.scan_port_threshold = 5  # unique ports before it's a "scan"

    # ==========================================
    # FLOW KEY
    # ==========================================

    def get_flow_key(self, packet):

        if not packet.haslayer("IP"):

            return None

        ip = packet["IP"]

        src_ip = ip.src
        dst_ip = ip.dst

        protocol = ip.proto

        src_port = 0
        dst_port = 0

        if packet.haslayer("TCP"):

            src_port = packet["TCP"].sport
            dst_port = packet["TCP"].dport

        elif packet.haslayer("UDP"):

            src_port = packet["UDP"].sport
            dst_port = packet["UDP"].dport

        endpoints = sorted([
            (src_ip, src_port),
            (dst_ip, dst_port)
        ])

        return (
            endpoints[0][0],
            endpoints[1][0],
            endpoints[0][1],
            endpoints[1][1],
            protocol
        )

    # ==========================================
    # ADD PACKET
    # ==========================================

    def add_packet(self, packet):

        flow_key = self.get_flow_key(
            packet
        )

        if flow_key is None:

            return

        now = time.time()

        flow = self.flows[
            flow_key
        ]

        flow["flow_key"] = flow_key

        if flow["first_seen"] is None:

            flow["first_seen"] = now

        flow["last_seen"] = now

        flow["packets"].append(
            packet
        )

        # ── Track potential port scans ──
        self._track_scan(packet, now)

    # ==========================================
    # PORT SCAN TRACKER
    # ==========================================

    def _track_scan(self, packet, now):
        """Track SYN probes to detect port scanning behaviour."""
        if not packet.haslayer("IP"):
            return
        if not packet.haslayer("TCP"):
            return

        tcp = packet["TCP"]
        # Only track SYN packets (flag 0x02) — the hallmark of a port scan
        if tcp.flags != 0x02 and tcp.flags != "S":
            return

        ip = packet["IP"]
        src_ip = ip.src
        dst_ip = ip.dst
        dst_port = tcp.dport

        tracker = self.scan_tracker[src_ip]
        if tracker["first_seen"] is None:
            tracker["first_seen"] = now
        tracker["last_seen"] = now
        tracker["dest_ports"].add(dst_port)
        tracker["packets"].append(packet)
        tracker["dest_ip"] = dst_ip

    # ==========================================
    # EXPIRE FLOWS
    # ==========================================

    def expire_flows(self):

        now = time.time()

        completed = []

        expired_keys = []

        for flow_key, flow in (
            self.flows.items()
        ):

            idle_time = (
                now -
                flow["last_seen"]
            )
            
            active_time = (
                now - 
                flow["first_seen"]
            )

            # Expire if idle, OR if it has been active for too long (e.g. ongoing DDoS)
            if idle_time > self.flow_timeout or active_time > self.active_timeout:

                expired_keys.append(
                    flow_key
                )

        for key in expired_keys:

            completed.append(
                self.flows.pop(key)
            )

        # ── Check for port scan meta-flows ──
        scan_flows = self._expire_scans(now)
        completed.extend(scan_flows)

        return completed

    # ==========================================
    # EXPIRE SCANS → META-FLOWS
    # ==========================================

    def _expire_scans(self, now):
        """Convert expired port scan trackers into meta-flows for the ML pipeline."""
        meta_flows = []
        expired_src_ips = []

        for src_ip, tracker in self.scan_tracker.items():
            idle = now - tracker["last_seen"]
            elapsed = now - tracker["first_seen"]

            # Only emit if the scan window expired AND enough unique ports were probed
            if idle > self.scan_window or elapsed > self.scan_window:
                unique_ports = len(tracker["dest_ports"])

                if unique_ports >= self.scan_port_threshold:
                    # Build a synthetic meta-flow that the ML pipeline can detect
                    meta_flow = {
                        "first_seen": tracker["first_seen"],
                        "last_seen": tracker["last_seen"],
                        "packets": tracker["packets"],
                        "flow_key": (
                            src_ip,
                            tracker["dest_ip"] or "0.0.0.0",
                            0,       # source port varies
                            0,       # destination port varies
                            6        # TCP
                        ),
                        "_is_portscan": True,
                        "_unique_ports": unique_ports,
                    }
                    print(
                        f"[SCAN] Port scan detected from {src_ip}: "
                        f"{unique_ports} unique ports probed, "
                        f"{len(tracker['packets'])} SYN packets"
                    )
                    meta_flows.append(meta_flow)

                expired_src_ips.append(src_ip)

        for ip in expired_src_ips:
            del self.scan_tracker[ip]

        return meta_flows