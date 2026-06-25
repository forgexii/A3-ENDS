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

        duration = 0.0

        if len(timestamps) > 1:

            duration = float(

                max(timestamps)
                -
                min(timestamps)

            )

        packet_count = len(
            packet_sizes
        )

        mean_packet_size = float(
            np.mean(packet_sizes)
        )

        std_packet_size = float(
            np.std(packet_sizes)
        )

        total_bytes = float(
            np.sum(packet_sizes)
        )

        mean_iat = 0.0

        if len(timestamps) > 1:

            iats = np.diff(
                timestamps
            )

            mean_iat = float(
                np.mean(iats)
            )

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