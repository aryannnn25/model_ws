#!/usr/bin/env python3

import os
import time
import math
import threading
from collections import deque

# --- Headless Matplotlib Setup ---
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import numpy as np
from sklearn.cluster import DBSCAN

# --- ROS 2 & Flask Imports ---
import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage
from flask import Flask

# ─── ABSOLUTE PATH RESOLUTION ──────────────────────────────────────────
# This forces Flask and Matplotlib to look at the exact same folder location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(SCRIPT_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# --- EXACT SAME NOISE MITIGATION THRESHOLDS ---
MIN_VELOCITY_M_S = 0.3    
MIN_RCS_DBSM     = -20.0  
MIN_HITS         = 3      
TARGET_TIMEOUT   = 0.5    
DBSCAN_EPSILON   = 1.5    

# --- Flask Server Setup (Pointing explicitly to our absolute static folder) ---
app = Flask(__name__, static_folder=STATIC_DIR)

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Jetson Orin NX - Radar Monitor</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #1e1e1e; color: #ffffff; text-align: center; padding: 20px; }
            .container { display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin-top: 20px; }
            .plot-box { background-color: #2d2d2d; padding: 15px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.5); }
            img { max-width: 100%; height: auto; border-radius: 4px; background-color: #1e1e1e; }
        </style>
        <script>
            // Smoothly reload images by appending a cache-busting timestamp
            setInterval(function() {
                var timestamp = new Date().getTime();
                document.getElementById('xy_plot').src = '/static/radar_xy.png?t=' + timestamp;
                document.getElementById('rcs_plot').src = '/static/radar_rcs.png?t=' + timestamp;
            }, 100); 
        </script>
    </head>
    <body>
        <h1>Live Radar Tracking Dashboard</h1>
        <p>Streaming from Jetson Orin NX Node</p>
        <div class="container">
            <div class="plot-box">
                <h3>Spatial Clustering (DBSCAN)</h3>
                <img id="xy_plot" src="/static/radar_xy.png" width="550" alt="Waiting for radar data...">
            </div>
            <div class="plot-box">
                <h3>RCS Over Time</h3>
                <img id="rcs_plot" src="/static/radar_rcs.png" width="550" alt="Waiting for radar data...">
            </div>
        </div>
    </body>
    </html>
    """

# Note: We removed the custom /static route because Flask handles it 
# automatically when `static_folder` is supplied in the initializer.


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
        self.get_logger().info("Radar Filter Node started. Web server plotting armed.")

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

        if x_m < 10.0 and not self.alert_latched:
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


def run_plots(node: RadarFilterNode):
    """Generates plots in a background thread and saves them using atomic replacements."""
    
    # Define absolute target image paths and temporary paths
    xy_final  = os.path.join(STATIC_DIR, "radar_xy.png")
    xy_tmp    = os.path.join(STATIC_DIR, "radar_xy_tmp.png")
    rcs_final = os.path.join(STATIC_DIR, "radar_rcs.png")
    rcs_tmp   = os.path.join(STATIC_DIR, "radar_rcs_tmp.png")

    fig_xy, ax_xy = plt.subplots()
    scatter = ax_xy.scatter([], [], cmap='tab10', vmin=-1, vmax=9)
    ax_xy.set_xlabel("Y (m)")
    ax_xy.set_ylabel("X (m)")
    ax_xy.set_title("Radar Targets (Clustered & Denoised)")
    ax_xy.set_xlim(-15, 15)
    ax_xy.set_ylim(0, 30)
    ax_xy.grid(True)

    fig_rcs, ax_rcs = plt.subplots()
    rcs_line, = ax_rcs.plot([], [])
    ax_rcs.set_xlabel("Time (s)")
    ax_rcs.set_ylabel("RCS (dBsm)")
    ax_rcs.set_title("RCS Over Time (Filtered Objects)")
    ax_rcs.grid(True)

    while rclpy.ok():
        valid_xs, valid_ys = [], []

        with node.targets_lock:
            for tid, data in node.targets.items():
                if data['hits'] >= MIN_HITS:
                    valid_xs.append(data['x'])
                    valid_ys.append(data['y'])

        if len(valid_xs) > 0:
            X_coords = np.column_stack((valid_xs, valid_ys))
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

        # ── ATOMIC SAVE PATTERN ──────────────────────────────────────────
        # 1. Save to a temporary file first
        fig_xy.savefig(xy_tmp, bbox_inches='tight', dpi=100)
        fig_rcs.savefig(rcs_tmp, bbox_inches='tight', dpi=100)
        
        # 2. Instantly rename them. This swap is atomic at the OS level, 
        # so Flask never tries to read a half-written file.
        try:
            os.replace(xy_tmp, xy_final)
            os.replace(rcs_tmp, rcs_final)
        except Exception:
            pass # Prevent race condition crashes during closing

        time.sleep(0.1) 

    plt.close("all")


def main(args=None):
    rclpy.init(args=args)
    node = RadarFilterNode()

    plot_thread = threading.Thread(target=run_plots, args=(node,), daemon=True)
    plot_thread.start()

    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), 
        daemon=True
    )
    flask_thread.start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()