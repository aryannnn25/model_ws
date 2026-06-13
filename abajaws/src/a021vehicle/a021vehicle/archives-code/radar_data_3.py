#!/usr/bin/env python3
import time
import math
import threading
from collections import deque

import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage
from std_msgs.msg import Int32

# --- EXACT SAME NOISE MITIGATION THRESHOLDS AS radar.py ---
MIN_VELOCITY_M_S = 0.3    # Ignore targets moving slower than 0.3 m/s
MIN_RCS_DBSM     = -20.0  # Ignore highly unreflective targets
MIN_HITS         = 3      # Target must be seen this many times before publishing
TARGET_TIMEOUT   = 0.5    # Seconds before a stale target is dropped


class RadarFilterNode(Node):
    def __init__(self):
        super().__init__('radar_filter_node')

        # Internal target tracker
        self.targets      = {}
        self.targets_lock = threading.Lock()

        # The Latching Switch
        self.alert_latched = False 

        # Subscriber & Publishers
        self.subscription = self.create_subscription(RadarMessage, '/rawradar', self.raw_radar_callback, 10)
        self.publisher = self.create_publisher(RadarMessage, '/radar_data', 10)
        self.phase_publisher = self.create_publisher(Int32, '/phase_id', 10)

        self.create_timer(0.1, self.purge_stale_targets)

        self.get_logger().info("Radar Filter Node started. Latched switch ready.")

    def purge_stale_targets(self):
        now = time.time()
        with self.targets_lock:
            stale = [
                tid for tid, data in self.targets.items()
                if now - data['last_seen'] > TARGET_TIMEOUT
            ]
            for tid in stale:
                self.get_logger().debug(f"Dropping stale target ID {tid}")
                del self.targets[tid]

    def raw_radar_callback(self, msg: RadarMessage):
        target_id = msg.target_id
        x_m       = msg.x
        y_m       = msg.y
        v_m_s     = msg.v
        rcs       = msg.rcs
        r_m       = msg.r
        angle_deg = msg.angle

        # ── Filter 1 & 2: Denoising ──────────────────────────────────────
        if abs(v_m_s) < MIN_VELOCITY_M_S or rcs < MIN_RCS_DBSM:
            return
        if y_m < -3.5 or y_m > 3.5:
            return

        # ── Temporal tracking ────────────────────────────────────────────
        now = time.time()
        with self.targets_lock:
            hits = self.targets[target_id]['hits'] + 1 if target_id in self.targets else 1

            self.targets[target_id] = {
                'x': x_m, 'y': y_m, 'v': v_m_s, 'rcs': rcs, 
                'r': r_m, 'angle': angle_deg, 'last_seen': now, 'hits': hits
            }

        if hits < MIN_HITS:
            return

        # ── ADDED PRINT STATEMENT: Always logs valid target details ─────
        current_state_str = "LATCHED [-1]" if self.alert_latched else "NORMAL [1]"
        self.get_logger().info(
            f"[{current_state_str}] TRACKING ID: {target_id:3d} | "
            f"Pos: ({x_m:6.2f}m, {y_m:6.2f}m) | "
            f"Vel: {v_m_s:6.2f}m/s | "
            f"Range: {r_m:6.2f}m | "
            f"Hits: {hits}"
        )

        # ── Latching Alert Logic ─────────────────────────────────────────
        if x_m < 10.0 and (-1.75 < y_m < 1.75):
            if not self.alert_latched:  # Only print the error once when it first trips
                self.get_logger().error(f"CRITICAL ALERT: Target {target_id} breached 10m! Switch locked to -1.")
                self.alert_latched = True

        # Publish the phase state (Will stay -1 once latched)
        phase_msg = Int32()
        phase_msg.data = -1 if self.alert_latched else 1
        self.phase_publisher.publish(phase_msg)

        # ── Forward the clean radar data ─────────────────────────────────
        filtered_msg = RadarMessage()
        filtered_msg.target_id = target_id
        filtered_msg.x = x_m
        filtered_msg.y = y_m
        filtered_msg.v = v_m_s
        filtered_msg.rcs = rcs
        filtered_msg.r = r_m
        filtered_msg.angle = angle_deg

        self.publisher.publish(filtered_msg)

def main(args=None):
    rclpy.init(args=args)
    node = RadarFilterNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()