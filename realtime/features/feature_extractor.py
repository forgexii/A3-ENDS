"""
Feature Extractor

Converts completed flows into
the feature vector expected by
the realtime ML models.
"""

import numpy as np


class FeatureExtractor:

    def __init__(self):

        self.feature_order = [

            "duration",

            "packet_count",

            "mean_packet_size",

            "std_packet_size",

            "total_bytes",

            "mean_iat"
        ]

    # ==========================================
    # EXTRACT FEATURES
    # ==========================================

    def extract(
        self,
        flow
    ):

        packets = flow["packets"]

        flow_key = flow["flow_key"]

        src_ip = flow_key[0]
        dst_ip = flow_key[1]

        src_port = flow_key[2]
        dst_port = flow_key[3]

        protocol = flow_key[4]

        timestamps = []

        packet_sizes = []

        for packet in packets:

            timestamps.append(
                float(packet.time)
            )

            packet_sizes.append(
                len(packet)
            )

        duration_sec = 0.0
        duration = 0.0

        if len(timestamps) > 1:
            duration_sec = float(max(timestamps) - min(timestamps))
            # CICIDS2017 Flow Duration is in microseconds
            duration = float(duration_sec * 1e6)

        packet_count = len(packet_sizes)
        
        mean_packet_size = float(np.mean(packet_sizes)) if packet_sizes else 0.0
        std_packet_size = float(np.std(packet_sizes)) if packet_sizes else 0.0

        total_bytes_sum = float(np.sum(packet_sizes)) if packet_sizes else 0.0
        # CICIDS2017 "total_bytes" was mapped to "Flow Bytes/s"
        total_bytes = 0.0
        if duration_sec > 0:
            total_bytes = float(total_bytes_sum / duration_sec)

        mean_iat = 0.0

        if len(timestamps) > 1:
            iats = np.diff(timestamps)
            # CICIDS2017 Flow IAT Mean is in microseconds
            mean_iat = float(np.mean(iats) * 1e6)

        # ── Port Scan Amplification ──
        # If this is a port scan meta-flow, the raw per-packet features
        # are misleadingly small. Amplify using the aggregated scan stats.
        if flow.get("_is_portscan"):
            unique_ports = flow.get("_unique_ports", 1)
            # A port scan hitting 100+ ports in seconds is extremely anomalous
            # Scale total_bytes by unique ports to reflect the scanning volume
            total_bytes = float(packet_count * mean_packet_size * unique_ports)
            # Reflect rapid-fire probing in the packet count
            packet_count = max(packet_count, unique_ports)

        return {

            # ==================================
            # FLOW METADATA
            # ==================================

            "source_ip":
                src_ip,

            "destination_ip":
                dst_ip,

            "source_port":
                src_port,

            "destination_port":
                dst_port,

            "protocol":
                protocol,

            "flow_start":
                flow["first_seen"],

            "flow_end":
                flow["last_seen"],

            # ==================================
            # ML FEATURES
            # ==================================

            "duration":
                duration,

            "packet_count":
                packet_count,

            "mean_packet_size":
                mean_packet_size,

            "std_packet_size":
                std_packet_size,

            "total_bytes":
                total_bytes,

            "mean_iat":
                mean_iat
        }