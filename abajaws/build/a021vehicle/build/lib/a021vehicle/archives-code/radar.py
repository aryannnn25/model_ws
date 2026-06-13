import threading
import time
import math
from ctypes import *
from datetime import datetime
from collections import deque
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

# Load the USBCAN library
# lib = cdll.LoadLibrary("./dependencies/libusbcan.so")
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Check if the .so file is in a 'dependencies' subfolder (like when running in src/) 
#    or right next to the script (like when running in install/)
if os.path.exists(os.path.join(current_dir, "dependencies", "libusbcan.so")):
    lib_path = os.path.join(current_dir, "dependencies", "libusbcan.so")
else:
    lib_path = os.path.join(current_dir, "libusbcan.so")

# 3. Load the library safely using its absolute path
print(f"Loading driver library from: {lib_path}")
lib = cdll.LoadLibrary(lib_path)
USBCAN_I = c_uint32(3)    # USBCAN-I/I+

USBCAN_II = c_uint32(4)   # USBCAN-II/II+
MAX_CHANNELS = 2

# Run flag
g_thd_run = 1

# --- NOISE MITIGATION THRESHOLDS ---
MIN_VELOCITY_M_S = 0.3    # Ignore targets moving slower than 0.3 m/s (removes static walls/trees)
MIN_RCS_DBSM = -20.0      # Ignore highly unreflective targets (removes phantom noise)
MIN_HITS = 3              # Target must be seen this many times consecutively before plotting
TARGET_TIMEOUT = 0.5      # Seconds before a stale target is dropped
DBSCAN_EPSILON = 2.0      # Max distance (meters) between points to group them into one object

# Track targets by ID: {target_id: {'x': x, 'y': y, 'v': v, 'rcs': rcs, 'last_seen': time, 'hits': count}}
targets = {}
targets_lock = threading.Lock()

# RCS history for graph: stores (timestamp, rcs, target_id)
rcs_history = deque(maxlen=1000)
rcs_lock = threading.Lock()


class ZCAN_CAN_INIT_CONFIG(Structure):
    _fields_ = [
        ("AccCode", c_int),
        ("AccMask", c_int),
        ("Reserved", c_int),
        ("Filter", c_ubyte),
        ("Timing0", c_ubyte),
        ("Timing1", c_ubyte),
        ("Mode", c_ubyte),
    ]


class ZCAN_CAN_OBJ(Structure):
    _fields_ = [
        ("ID", c_uint32),
        ("TimeStamp", c_uint32),
        ("TimeFlag", c_uint8),
        ("SendType", c_byte),
        ("RemoteFlag", c_byte),
        ("ExternFlag", c_byte),
        ("DataLen", c_byte),
        ("Data", c_ubyte * 8),
        ("Reserved", c_ubyte * 3),
    ]
def parse_and_store_sr73f_data(can_id, data_bytes):
    """
    Decode SR73F/MR72 payload, apply noise filtering, and store.
    """
    if can_id != 0x60b:
        return

    if len(data_bytes) < 8:
        return

    b0, b1, b2, b3, b4, b5, b6, b7 = data_bytes

    target_id = b0
    y_m = (b1 * 32 + (b2 >> 3)) * 0.2 - 500.0
    x_m = (((b2 & 0x07) * 256) + b3) * 0.2 - 204.6
    v_m_s = (b4 * 4 + (b5 >> 6)) * 0.25 - 128.0
    rcs = b7 * 0.5 - 64.0

    # 1. Static Clutter, RCS, & Spatial Filter
    if abs(v_m_s) < MIN_VELOCITY_M_S or rcs < MIN_RCS_DBSM:
        return
        
    # Ignore targets outside the Y-axis range of -3.5m to 3.5m
    if y_m < -3.5 or y_m > 3.5:
        return

    r_m = math.sqrt(x_m ** 2 + y_m ** 2)
    angle_deg = math.degrees(math.atan2(x_m, y_m))
    now = time.time()

    # 2. Temporal Tracking (Hit Counter)
    with targets_lock:
        if target_id in targets:
            hits = targets[target_id]['hits'] + 1
        else:
            hits = 1
            
        targets[target_id] = {
            'x': x_m, 
            'y': y_m, 
            'v': v_m_s, 
            'rcs': rcs,
            'last_seen': now, 
            'hits': hits
        }

    # Only log RCS for targets that have survived the initial filters
    with rcs_lock:
        rcs_history.append((now, rcs, target_id))

    now_str = datetime.now().strftime("%Y_%m_%d %H:%M:%S.%f")[:-3]
    print(
        f"Time: {now_str}, ID: {target_id}, RCS: {rcs:.1f}, "
        f"X: {x_m:.2f}, Y: {y_m:.2f}, V: {v_m_s:.2f}, R: {r_m:.2f}, Hits : {hits}"
    )

    # --- NEW ALERT CODE ---
    # Trigger alert if the object has met the plot threshold and X is under 10m
    if hits >= MIN_HITS and x_m < 10.0:
        print(f"⚠️  ALERT: Object ID {target_id} is under 10 meters on the X-axis! (X: {x_m:.2f}m) ⚠️")

def rx_thread(dev_type, dev_idx, chn_idx):
    global g_thd_run
    print("Listening for radar data (Filtered)...")

    while g_thd_run == 1:
        time.sleep(0.01)
        count = lib.VCI_GetReceiveNum(dev_type, dev_idx, chn_idx)
        if count > 0:
            can = (ZCAN_CAN_OBJ * count)()
            rcount = lib.VCI_Receive(dev_type, dev_idx, chn_idx, byref(can), count, 100)

            for i in range(rcount):
                if can[i].RemoteFlag == 0:
                    raw_payload = bytes(can[i].Data[:can[i].DataLen])
                    parse_and_store_sr73f_data(can[i].ID, raw_payload)


def wait_for_exit():
    global g_thd_run
    input()
    g_thd_run = 0


def run_plots():
    """
    Run matplotlib in the MAIN thread with DBSCAN clustering.
    """
    plt.ion()

    # Window 1: XY scatter
    fig_xy, ax_xy = plt.subplots()
    # Use a colormap to differentiate DBSCAN clusters
    scatter = ax_xy.scatter([], [], cmap='tab10', vmin=-1, vmax=9)

    ax_xy.set_xlabel("X (m)")
    ax_xy.set_ylabel("Y (m)")
    ax_xy.set_title("Radar Targets (Clustered & Denoised)")
    ax_xy.set_xlim(-15, 15)
    ax_xy.set_ylim(0, 30)
    ax_xy.grid(True)

    # Window 2: RCS graph
    fig_rcs, ax_rcs = plt.subplots()
    rcs_line, = ax_rcs.plot([], [])

    ax_rcs.set_xlabel("Time (s)")
    ax_rcs.set_ylabel("RCS (dBsm)")
    ax_rcs.set_title("RCS Over Time (Filtered Objects)")
    ax_rcs.grid(True)

    while g_thd_run == 1:
        now = time.time()
        valid_xs, valid_ys = [], []

        with targets_lock:
            stale_ids = []
            for tid, data in targets.items():
                if now - data['last_seen'] > TARGET_TIMEOUT:
                    stale_ids.append(tid)
                # Only plot if the target has persisted for MIN_HITS
                elif data['hits'] >= MIN_HITS:
                    valid_xs.append(data['x'])
                    valid_ys.append(data['y'])

            for tid in stale_ids:
                del targets[tid]

        # 3. Spatial Clustering (DBSCAN)
        if len(valid_xs) > 0:
            X_coords = np.column_stack((valid_xs, valid_ys))
            
            # min_samples=1 so we don't drop isolated valid tracks, 
            # but groups nearby IDs into the same color "object"
            clustering = DBSCAN(eps=DBSCAN_EPSILON, min_samples=1).fit(X_coords)
            labels = clustering.labels_

            scatter.set_offsets(X_coords)
            scatter.set_array(labels) # Colors the dots based on cluster ID
        else:
            scatter.set_offsets(np.empty((0, 2)))

        with rcs_lock:
            rcs_data = list(rcs_history)

        if rcs_data:
            t0 = rcs_data[0][0]
            tx = [t - t0 for t, _, _ in rcs_data]
            rv = [rcs for _, rcs, _ in rcs_data]
            rcs_line.set_data(tx, rv)
            ax_rcs.relim()
            ax_rcs.autoscale_view()
        else:
            rcs_line.set_data([], [])

        fig_xy.canvas.draw_idle()
        fig_rcs.canvas.draw_idle()
        plt.pause(0.05)

    plt.close("all")


if __name__ == "__main__":
    threads = []

    gBaud = 0x1C00       # 500 kbps
    DevType = USBCAN_II
    DevIdx = 0

    ret = lib.VCI_OpenDevice(DevType, DevIdx, 0)
    if ret == 0:
        print("Open device fail. Please check USB connection and permissions.")
        raise SystemExit(1)

    print("Device opened successfully. Initializing CAN channels...")

    for i in range(MAX_CHANNELS):
        init_config = ZCAN_CAN_INIT_CONFIG()
        init_config.AccCode = 0
        init_config.AccMask = 0xFFFFFFFF
        init_config.Reserved = 0
        init_config.Filter = 1
        init_config.Timing0 = gBaud & 0xFF
        init_config.Timing1 = (gBaud >> 8) & 0xFF
        init_config.Mode = 0

        ret = lib.VCI_InitCAN(DevType, DevIdx, i, byref(init_config))
        if ret == 0:
            print(f"VCI_InitCAN failed on channel {i}")
            continue

        ret = lib.VCI_StartCAN(DevType, DevIdx, i)
        if ret == 0:
            print(f"VCI_StartCAN failed on channel {i}")
            continue

        t = threading.Thread(target=rx_thread, args=(DevType, DevIdx, i), daemon=True)
        threads.append(t)
        t.start()

    exit_thread = threading.Thread(target=wait_for_exit, daemon=True)
    exit_thread.start()

    print("Listening for SR73F Radar Data. Press ENTER to stop...")

    run_plots()

    g_thd_run = 0

    for t in threads:
        t.join(timeout=1.0)

    for i in range(MAX_CHANNELS):
        lib.VCI_ResetCAN(DevType, DevIdx, i)

    lib.VCI_CloseDevice(DevType, DevIdx)
    del lib

    print("Device closed.")
