#!/usr/bin/env python3
import time
import math
import threading
from collections import deque

import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage

import matplotlib
# matplotlib.use('TkAgg')           # interactive backend for live window
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation

# ─── NOISE MITIGATION THRESHOLDS ─────────────────────────────────────────────
MIN_VELOCITY_M_S = 0.3     # Ignore targets moving slower than 0.3 m/s
MIN_RCS_DBSM     = -20.0   # Ignore highly unreflective targets
MIN_HITS         = 3       # Target must be seen N times before publishing
TARGET_TIMEOUT   = 1.5     # Seconds before a stale target is dropped (was 0.5)

# ─── DANGER ZONE (for plot colouring & downstream consumers) ─────────────────
DANGER_X_MAX     = 6.0     # metres — forward distance threshold
DANGER_Y_ABS     = 1.5     # metres — lateral half-width


class RadarFilterNode(Node):
    def __init__(self):
        super().__init__('radar_filter_node')

        # Internal target tracker:  target_id → {x, y, v, rcs, r, angle,
        #                                        last_seen, hits, confirmed}
        self.targets      = {}
        self.targets_lock = threading.Lock()

        # Subscriber & Publisher
        self.subscription = self.create_subscription(
            RadarMessage, '/rawradar', self.raw_radar_callback, 10)
        self.publisher = self.create_publisher(RadarMessage, '/radar_data', 10)

        # Timer for purging stale targets
        self.create_timer(0.1, self.purge_stale_targets)

        self.get_logger().info("Radar Filter Node started.")

    # ── Purge stale targets ──────────────────────────────────────────────
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

    # ── Raw radar callback ───────────────────────────────────────────────
    def raw_radar_callback(self, msg: RadarMessage):
        target_id = msg.target_id
        x_m       = msg.x
        y_m       = msg.y
        v_m_s     = msg.v
        rcs       = msg.rcs
        r_m       = msg.r
        angle_deg = msg.angle

        # ── Filter 1 & 2: Denoising (velocity + RCS) ────────────────────
        if abs(v_m_s) < MIN_VELOCITY_M_S or rcs < MIN_RCS_DBSM:
            return

        # ── Temporal tracking ────────────────────────────────────────────
        now = time.time()
        with self.targets_lock:
            existing = self.targets.get(target_id)

            if existing is not None:
                hits      = existing['hits'] + 1
                confirmed = existing['confirmed'] or (hits >= MIN_HITS)
            else:
                hits      = 1
                confirmed = False

            self.targets[target_id] = {
                'x': x_m, 'y': y_m, 'v': v_m_s, 'rcs': rcs,
                'r': r_m, 'angle': angle_deg,
                'last_seen': now, 'hits': hits, 'confirmed': confirmed,
            }

        # Don't publish until confirmed
        if not confirmed:
            return

        # ── Spatial filter: only publish targets in the lane corridor ────
        in_danger = (x_m < DANGER_X_MAX) and (-DANGER_Y_ABS < y_m < DANGER_Y_ABS)

        # Log
        zone_str = "DANGER" if in_danger else "NORMAL"
        self.get_logger().info(
            f"[{zone_str}] ID: {target_id:3d} | "
            f"Pos: ({x_m:6.2f}m, {y_m:6.2f}m) | "
            f"Vel: {v_m_s:6.2f}m/s | "
            f"Range: {r_m:6.2f}m"
        )

        # ── Forward the clean radar data ─────────────────────────────────
        filtered_msg = RadarMessage()
        filtered_msg.target_id = target_id
        filtered_msg.x         = x_m
        filtered_msg.y         = y_m
        filtered_msg.v         = v_m_s
        filtered_msg.rcs       = rcs
        filtered_msg.r         = r_m
        filtered_msg.angle     = angle_deg

        self.publisher.publish(filtered_msg)


# ═════════════════════════════════════════════════════════════════════════════
# LIVE MATPLOTLIB PLOT
# ═════════════════════════════════════════════════════════════════════════════

def run_live_plot(node: RadarFilterNode):
    """
    Runs a live matplotlib scatter plot in the main thread.
    Blue markers  = all confirmed targets
    Red  markers  = targets inside the danger zone (-1.5 < y < 1.5 AND x < 6)
    A translucent red rectangle visualises the danger zone on the plot.
    """
    fig, ax = plt.subplots(figsize=(9, 7))
    fig.canvas.manager.set_window_title('Radar Target Plot')

    # Persistent scatter handles (empty at start)
    scat_normal = ax.scatter([], [], c='dodgerblue', s=60, label='Target',
                             edgecolors='white', linewidths=0.5, zorder=3)
    scat_danger = ax.scatter([], [], c='red', s=90, marker='X',
                             label='DANGER zone', edgecolors='white',
                             linewidths=0.5, zorder=4)

    # Draw the danger zone rectangle  (x: 0→6,  y: -1.5→1.5)
    danger_rect = patches.Rectangle(
        (0, -DANGER_Y_ABS), DANGER_X_MAX, 2 * DANGER_Y_ABS,
        linewidth=1.5, edgecolor='red', facecolor='red', alpha=0.10,
        linestyle='--', label='Danger zone', zorder=1)
    ax.add_patch(danger_rect)

    ax.set_xlabel('X  (forward distance) [m]', fontsize=11)
    ax.set_ylabel('Y  (lateral offset)   [m]', fontsize=11)
    ax.set_title('Radar Detections — Live', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    ax.set_xlim(-5, 50)
    ax.set_ylim(-10, 10)
    ax.set_aspect('equal', adjustable='datalim')
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color='grey', linewidth=0.5)
    ax.axvline(0, color='grey', linewidth=0.5)

    def update(_frame):
        with node.targets_lock:
            # Only show confirmed targets
            confirmed = {
                tid: d for tid, d in node.targets.items() if d['confirmed']
            }

        if not confirmed:
            scat_normal.set_offsets([])
            scat_danger.set_offsets([])
            ax.set_title('Radar Detections — Live  (no targets)', fontsize=13,
                         fontweight='bold')
            return scat_normal, scat_danger

        normal_pts = []
        danger_pts = []

        for tid, d in confirmed.items():
            x, y = d['x'], d['y']
            in_danger = (x < DANGER_X_MAX) and (-DANGER_Y_ABS < y < DANGER_Y_ABS)
            if in_danger:
                danger_pts.append((x, y))
            else:
                normal_pts.append((x, y))

        import numpy as np
        scat_normal.set_offsets(np.array(normal_pts) if normal_pts
                                else np.empty((0, 2)))
        scat_danger.set_offsets(np.array(danger_pts) if danger_pts
                                else np.empty((0, 2)))

        n_total  = len(confirmed)
        n_danger = len(danger_pts)
        ax.set_title(f'Radar Detections — Live  '
                     f'({n_total} targets, {n_danger} in danger zone)',
                     fontsize=13, fontweight='bold')

        return scat_normal, scat_danger

    _anim = FuncAnimation(fig, update, interval=100, blit=False, cache_frame_data=False)
    plt.tight_layout()
    # plt.show()


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main(args=None):
    rclpy.init(args=args)
    node = RadarFilterNode()

    # Spin ROS2 in a background thread so matplotlib can own the main thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        run_live_plot(node)          # blocks until the plot window is closed
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()