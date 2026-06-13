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
DBSCAN_EPSILON   = 2.0    # Kept as constant for reference (no clustering needed without plot)


class RadarFilterNode(Node):
    def __init__(self):
        super().__init__('radar_filter_node')

        # Internal target tracker: {target_id: {x, y, v, rcs, r, angle, last_seen, hits}}
        self.targets      = {}
        self.targets_lock = threading.Lock()

        # Subscriber — raw radar data
        self.subscription = self.create_subscription(
            RadarMessage,
            '/rawradar',
            self.raw_radar_callback,
            10
        )

        # Publisher — filtered radar data
        self.publisher = self.create_publisher(
            RadarMessage,
            '/radar_data',
            10
        )

        # Publisher — phase id
        self.phase_publisher = self.create_publisher(
            Int32,
            '/phase_id',
            10
        )

        self.create_timer(0.1, self.purge_stale_targets)

        self.get_logger().info(
            "Radar Filter Node started. "
            "Subscribing to /rawradar, publishing filtered data to /radar_data"
        )

    # ------------------------------------------------------------------
    # Stale target cleanup (mirrors the TARGET_TIMEOUT logic in radar.py)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Main callback — applies EXACT same filters as parse_and_store_sr73f_data()
    # ------------------------------------------------------------------
    def raw_radar_callback(self, msg: RadarMessage):
        target_id = msg.target_id
        x_m       = msg.x
        y_m       = msg.y
        v_m_s     = msg.v
        rcs       = msg.rcs
        r_m       = msg.r
        angle_deg = msg.angle

        # ── Filter 1: Static clutter & RCS threshold ──────────────────
        if abs(v_m_s) < MIN_VELOCITY_M_S or rcs < MIN_RCS_DBSM:
            return

        # ── Filter 2: Spatial / Y-axis lane filter ────────────────────
        if y_m < -3.5 or y_m > 3.5:
            return

        # ── Temporal tracking (hit counter) ───────────────────────────
        now = time.time()
        with self.targets_lock:
            if target_id in self.targets:
                hits = self.targets[target_id]['hits'] + 1
            else:
                hits = 1

            self.targets[target_id] = {
                'x':         x_m,
                'y':         y_m,
                'v':         v_m_s,
                'rcs':       rcs,
                'r':         r_m,
                'angle':     angle_deg,
                'last_seen': now,
                'hits':      hits,
            }

        # ── Filter 3: Minimum hit count before publishing ─────────────
        if hits < MIN_HITS:
            self.get_logger().debug(
                f"Target ID {target_id} suppressed — only {hits}/{MIN_HITS} hits so far"
            )
            return

        # ── Alert (mirrors the alert logic in radar.py) ───────────────
        # if x_m < 10.0 and (y_m<1.75 and y_m>-1.75):
        #     self.get_logger().warn(
        #         f"ALERT: Object ID {target_id} is under 10 meters! "
        #         f"(X: {x_m:.2f}m)"
        #     )
        #     phase_msg = Int32()
        #     phase_msg.data = -1
        #     self.phase_publisher.publish(phase_msg)
        # else:
        #     phase_msg = Int32()
        #     phase_msg.data = 1
        #     self.phase_publisher.publish(phase_msg)
    def publish_phase_state(self):
        danger = False
        
        with self.targets_lock:
            for tid, data in self.targets.items():
                # Check if any currently tracked valid target is in the danger zone
                if data['hits'] >= MIN_HITS:
                    if data['x'] < 10.0 and (-1.75 < data['y'] < 1.75):
                        danger = True
                        self.get_logger().warn(f"ALERT: Object ID {tid} is under 10 meters! (X: {data['x']:.2f}m)")
                        break # We only need one dangerous target to trigger braking
        
        # Publish -1 if in danger, otherwise 1
        phase_msg = Int32()
        phase_msg.data = -1 if danger else 1
        self.phase_publisher.publish(phase_msg)
        # ── Publish filtered message ───────────────────────────────────
        filtered_msg             = RadarMessage()
        filtered_msg.target_id   = target_id
        filtered_msg.x           = x_m
        filtered_msg.y           = y_m
        filtered_msg.v           = v_m_s
        filtered_msg.rcs         = rcs
        filtered_msg.r           = r_m
        filtered_msg.angle       = angle_deg

        self.publisher.publish(filtered_msg)

        self.get_logger().info(
            f"ID: {target_id:3d} | "
            f"Pos: ({x_m:6.2f}m, {y_m:6.2f}m) | "
            f"Vel: {v_m_s:6.2f}m/s | "
            f"RCS: {rcs:5.1f}dBsm | "
            f"Range: {r_m:6.2f}m | "
            f"Angle: {angle_deg:6.2f}° | "
            f"Hits: {hits}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = RadarFilterNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Filter node shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()