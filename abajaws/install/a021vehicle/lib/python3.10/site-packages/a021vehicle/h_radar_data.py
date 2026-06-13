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
MIN_VELOCITY_M_S = 0.3
MIN_RCS_DBSM     = -20.0
MIN_HITS         = 5
TARGET_TIMEOUT   = 0.5      # seconds
DBSCAN_EPSILON   = 0.4      # meters


class KalmanFilter2D:
    """
    Simple 2D constant-velocity Kalman filter
    State: [x, y, vx, vy]^T
    Measurement: [x, y]^T
    """
    def __init__(self, dt=0.1, process_var=0.05, meas_var=0.2):
        self.dt = dt

        # State vector [x, y, vx, vy]^T
        self.x = np.zeros((4, 1), dtype=float)

        # State transition matrix
        self.F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1,  0],
            [0, 0, 0,  1]
        ], dtype=float)

        # Measurement matrix: we measure only position
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=float)

        # State covariance
        self.P = np.diag([1.0, 1.0, 10.0, 10.0]).astype(float)

        # Measurement noise covariance
        self.R = np.array([
            [meas_var, 0],
            [0, meas_var]
        ], dtype=float)

        # Process noise covariance
        q = process_var
        self.Q = np.array([
            [q, 0, 0, 0],
            [0, q, 0, 0],
            [0, 0, q, 0],
            [0, 0, 0, q]
        ], dtype=float)

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x

    def update(self, z):
        z = np.array(z, dtype=float).reshape(2, 1)
        y = z - (self.H @ self.x)
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P
        return self.x

    def set_initial_state(self, x, y, vx=0.0, vy=0.0):
        self.x = np.array([[x], [y], [vx], [vy]], dtype=float)

    def get_position(self):
        return float(self.x[0, 0]), float(self.x[1, 0])

    def get_velocity(self):
        return float(self.x[2, 0]), float(self.x[3, 0])


class RadarFilterNode(Node):
    def __init__(self):
        super().__init__('radar_filter_node')

        self.targets = {}
        self.rcs_history = deque(maxlen=200)
        self.targets_lock = threading.Lock()
        self.alert_latched = False

        self.subscription = self.create_subscription(
            RadarMessage,
            '/rawradar',
            self.raw_radar_callback,
            10
        )
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
            if target_id in self.targets:
                hits = self.targets[target_id]['hits'] + 1
                kf = self.targets[target_id]['kf']

                # Predict then update with current radar position measurement
                kf.predict()
                kf.update([x_m, y_m])

            else:
                hits = 1
                kf = KalmanFilter2D(dt=0.1, process_var=0.05, meas_var=0.2)
                kf.set_initial_state(x_m, y_m, 0.0, 0.0)

            fx, fy = kf.get_position()
            fvx, fvy = kf.get_velocity()
            f_speed = math.hypot(fvx, fvy)

            self.targets[target_id] = {
                'x': fx,
                'y': fy,
                'v': f_speed,
                'rcs': rcs,
                'r': math.hypot(fx, fy),
                'angle': math.degrees(math.atan2(fy, fx)),
                'last_seen': now,
                'hits': hits,
                'kf': kf,
                'raw_x': x_m,
                'raw_y': y_m,
                'raw_v': v_m_s,
                'raw_r': r_m,
                'raw_angle': angle_deg
            }

            if hits >= MIN_HITS:
                self.rcs_history.append((now, rcs, target_id))

        if hits < MIN_HITS:
            return

        if (-1.7 < fy < 1.7) and (fx < 10.0 and not self.alert_latched):
            self.alert_latched = True

        filtered_msg = RadarMessage()
        filtered_msg.target_id = target_id
        filtered_msg.x = fx
        filtered_msg.y = fy
        filtered_msg.v = f_speed
        filtered_msg.rcs = rcs
        filtered_msg.r = math.hypot(fx, fy)
        filtered_msg.angle = math.degrees(math.atan2(fy, fx))

        self.publisher.publish(filtered_msg)


def run_plots_live(node: RadarFilterNode):
    """Generates live plots directly in windows, rotated 90 degrees."""

    plt.ion()

    fig_xy, ax_xy = plt.subplots()
    scatter = ax_xy.scatter([], [], cmap='tab10', vmin=-1, vmax=9)

    ax_xy.set_xlabel("Y - Lateral Offset (m)")
    ax_xy.set_ylabel("X - Longitudinal Distance (m)")
    ax_xy.set_title("Radar Targets (Bird's-Eye View) - Kalman Smoothed")
    ax_xy.set_xlim(-3, 3)
    ax_xy.set_ylim(0, 40)
    ax_xy.grid(True)

    fig_rcs, ax_rcs = plt.subplots()
    rcs_line, = ax_rcs.plot([], [])
    ax_rcs.set_xlabel("Time (s)")
    ax_rcs.set_ylabel("RCS (dBsm)")
    ax_rcs.set_title("RCS Over Time (Filtered Objects)")
    ax_rcs.grid(True)

    plt.show()

    while rclpy.ok():
        valid_xs, valid_ys = [], []

        with node.targets_lock:
            for tid, data in node.targets.items():
                if data['hits'] >= MIN_HITS:
                    if -1.7 < data['y'] < 1.7:
                        valid_xs.append(data['x'])   # filtered x
                        valid_ys.append(data['y'])   # filtered y

        if len(valid_xs) > 0:
            X_coords = np.column_stack((valid_ys, valid_xs))

            clustering = DBSCAN(eps=DBSCAN_EPSILON, min_samples=1).fit(X_coords)
            labels = clustering.labels_
            scatter.set_offsets(X_coords)
            scatter.set_array(labels)
        else:
            scatter.set_offsets(np.empty((0, 2)))
            scatter.set_array(np.array([]))

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

        try:
            plt.pause(0.1)
        except Exception:
            break

    plt.close("all")


def main(args=None):
    rclpy.init(args=args)
    node = RadarFilterNode()

    # Run ROS 2 spin in a background thread so it doesn't block Matplotlib
    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    try:
        run_plots_live(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()