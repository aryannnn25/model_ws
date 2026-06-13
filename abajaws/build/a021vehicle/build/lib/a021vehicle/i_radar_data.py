#!/usr/bin/env python3

import time
import math
import threading
from collections import deque

# --- Matplotlib Setup (Interactive Mode) ---
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import DBSCAN

# --- ROS 2 Imports ---
import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage

# --- EXACT SAME NOISE MITIGATION THRESHOLDS ---
MIN_VELOCITY_M_S = 0.3    # >0.5 m/s
MIN_RCS_DBSM     = -20.0    # >-20 dBsm
MIN_HITS         = 5       # publish/display after 3 hits
TARGET_TIMEOUT   = 0.5      # seconds
DBSCAN_EPSILON   =  0.4    # meters


class RadarFilterNode(Node):
    def __init__(self):
        super().__init__('radar_filter_node')

        self.targets = {}
        self.rcs_history = deque(maxlen=200) 
        self.targets_lock = threading.Lock()
        self.alert_latched = False 

        self.subscription = self.create_subscription(RadarMessage, '/rawradar', self.raw_radar_callback, 10)
        self.publisher = self.create_publisher(RadarMessage, '/radar_data', 10)

        self.create_timer(0.1, self.purge_stale_targets)
        self.get_logger().info("Radar Filter Node started. Live GUI plotting armed.")

    def purge_stale_targets(self):
        now = time.time()
        with self.targets_lock:
            stale = [
                tid for tid, data in self.targets.items()
                if now - data['last_seen'] > TARGET_TIMEOUT
            ]
            for tid in stale:
                del self.targets[tid]

    def raw_radar_callback(self, msg: RadarMessage):
        target_id = msg.target_id
        x_m       = msg.x
        y_m       = msg.y
        v_m_s     = msg.v
        rcs       = msg.rcs
        r_m       = msg.r
        angle_deg = msg.angle

        if abs(v_m_s) < MIN_VELOCITY_M_S or rcs < MIN_RCS_DBSM:
            return

        now = time.time()
        with self.targets_lock:
            hits = self.targets[target_id]['hits'] + 1 if target_id in self.targets else 1
            
            self.targets[target_id] = {
                'x': x_m, 'y': y_m, 'v': v_m_s, 'rcs': rcs, 
                'r': r_m, 'angle': angle_deg, 'last_seen': now, 'hits': hits
            }
            
            if hits >= MIN_HITS:
                self.rcs_history.append((now, rcs, target_id))

        if hits < MIN_HITS:
            return

        if (-1.7 < y_m < 1.7) and (x_m < 10.0 and not self.alert_latched):
            self.alert_latched = True

        filtered_msg = RadarMessage()
        filtered_msg.target_id = target_id
        filtered_msg.x = x_m
        filtered_msg.y = y_m
        filtered_msg.v = v_m_s
        filtered_msg.rcs = rcs
        filtered_msg.r = r_m
        filtered_msg.angle = angle_deg
        
        self.publisher.publish(filtered_msg)


def run_plots_live(node: RadarFilterNode):
    """Generates live plots directly in windows, rotated 90 degrees."""
    
    # Turn on Matplotlib interactive mode
    plt.ion()

    fig_xy, ax_xy = plt.subplots()
    scatter = ax_xy.scatter([], [], cmap='tab10', vmin=-1, vmax=9)
    
    # ── Rotated Mapping Setup ──────────────────────────────────────────
    # Horizontal axis is now Y, Vertical axis is now X
    ax_xy.set_xlabel("Y - Lateral Offset (m)")
    ax_xy.set_ylabel("X - Longitudinal Distance (m)")
    ax_xy.set_title("Radar Targets (Bird's-Eye View)")
    ax_xy.set_xlim(-3, 3)
    ax_xy.set_ylim(0, 40)
    ax_xy.grid(True)

    fig_rcs, ax_rcs = plt.subplots()
    rcs_line, = ax_rcs.plot([], [])
    ax_rcs.set_xlabel("Time (s)")
    ax_rcs.set_ylabel("RCS (dBsm)")
    ax_rcs.set_title("RCS Over Time (Filtered Objects)")
    ax_rcs.grid(True)
    
    # Show the windows initially
    plt.show()

    while rclpy.ok():
        valid_xs, valid_ys = [], []

        with node.targets_lock:
            for tid, data in node.targets.items():
                if data['hits'] >= MIN_HITS:
                    # Apply the requested lane boundaries
                    if -1.7 < data['y'] < 1.7:
                        valid_xs.append(data['x'])
                        valid_ys.append(data['y'])

        if len(valid_xs) > 0:
            # IMPORTANT ROTATION CHANGE: 
            # np.column_stack takes (Horizontal_Array, Vertical_Array)
            # We pass (valid_ys, valid_xs) so Y tracks horizontally and X tracks vertically.
            X_coords = np.column_stack((valid_ys, valid_xs))
            
            clustering = DBSCAN(eps=DBSCAN_EPSILON, min_samples=1).fit(X_coords)
            labels = clustering.labels_
            scatter.set_offsets(X_coords)
            scatter.set_array(labels) 
        else:
            scatter.set_offsets(np.empty((0, 2)))

        with node.targets_lock:
            rcs_data = list(node.rcs_history)

        if rcs_data:
            t0 = rcs_data[0][0]
            tx = [t - t0 for t, _, _ in rcs_data]
            rv = [rcs for _, rcs, _ in rcs_data]
            rcs_line.set_data(tx, rv)
            ax_rcs.relim()
            ax_rcs.autoscale_view()
        else:
            rcs_line.set_data([], [])

        # plt.pause updates the figures and handles GUI events, replacing time.sleep()
        try:
            plt.pause(0.02) 
        except Exception:
            break # Break loop if user closes the window manually

    plt.close("all")


def main(args=None):
    rclpy.init(args=args)
    node = RadarFilterNode()

    # Run ROS 2 spin in a background thread so it doesn't block Matplotlib
    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    try:
        # Run live Matplotlib plotting in the main thread
        run_plots_live(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()