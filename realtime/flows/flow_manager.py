"""
Flow Manager

Groups packets into bidirectional
network flows.
"""

import time

from collections import defaultdict


class FlowManager:

    def __init__(self):

        self.flow_timeout = 5

        self.flows = defaultdict(
            lambda: {
                "first_seen": None,
                "last_seen": None,
                "packets": [],
                "flow_key": None
            }
        )

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

            if idle_time > self.flow_timeout:

                expired_keys.append(
                    flow_key
                )

        for key in expired_keys:

            completed.append(
                self.flows.pop(key)
            )

        return completed