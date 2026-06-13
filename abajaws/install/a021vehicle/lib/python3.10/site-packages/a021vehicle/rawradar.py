import os
import threading
import time
import math
from ctypes import *
from datetime import datetime

import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage

# Load the USBCAN library using a path relative to this file
_here = os.path.dirname(os.path.abspath(__file__))
lib = cdll.LoadLibrary(os.path.join(_here, "libusbcan.so"))

USBCAN_I  = c_uint32(3)
USBCAN_II = c_uint32(4)
MAX_CHANNELS = 2

g_thd_run = 1

class ZCAN_CAN_INIT_CONFIG(Structure):
    _fields_ = [
        ("AccCode",  c_int),
        ("AccMask",  c_int),
        ("Reserved", c_int),
        ("Filter",   c_ubyte),
        ("Timing0",  c_ubyte),
        ("Timing1",  c_ubyte),
        ("Mode",     c_ubyte),
    ]

class ZCAN_CAN_OBJ(Structure):
    _fields_ = [
        ("ID",          c_uint32),
        ("TimeStamp",   c_uint32),
        ("TimeFlag",    c_uint8),
        ("SendType",    c_byte),
        ("RemoteFlag",  c_byte),
        ("ExternFlag",  c_byte),
        ("DataLen",     c_byte),
        ("Data",        c_ubyte * 8),
        ("Reserved",    c_ubyte * 3),
    ]

class RadarPublisherNode(Node):
    def __init__(self):
        super().__init__('radar_node')
        self.publisher_ = self.create_publisher(RadarMessage, '/rawradar', 10)
        self.get_logger().info("Radar publisher node started, publishing on /rawradar")

    def publish_target(self, target_id, x_m, y_m, v_m_s, rcs, r_m, angle_deg):
        msg = RadarMessage()
        msg.target_id = int(target_id)
        msg.x         = float(x_m)
        msg.y         = float(y_m)
        msg.v         = float(v_m_s)
        msg.rcs       = float(rcs)
        msg.r         = float(r_m)
        msg.angle     = float(angle_deg)
        self.publisher_.publish(msg)
        
        # Uncomment the logger below if you want terminal output, 
        # but it might slow down high-frequency CAN reads
        # self.get_logger().info(
        #     f"ID: {target_id:3d} | "
        #     f"Pos: ({x_m:6.2f}m, {y_m:6.2f}m) | "
        #     f"Vel: {v_m_s:6.2f}m/s | "
        #     f"RCS: {rcs:5.1f}dBsm | "
        #     f"Range: {r_m:6.2f}m | "
        #     f"Angle: {angle_deg:6.2f}°"
        # )

def parse_and_publish(can_id, data_bytes, node: RadarPublisherNode):
    if can_id != 0x60b:
        return
    if len(data_bytes) < 8:
        return

    b0, b1, b2, b3, b4, b5, b6, b7 = data_bytes

    target_id = b0
    x_m       = (b1 * 32 + (b2 >> 3)) * 0.2 - 500.0          # DistLong (forward)
    y_m       = (((b2 & 0x07) * 256) + b3) * 0.2 - 204.6     # DistLat  (lateral)
    v_m_s     = (b4 * 4 + (b5 >> 6)) * 0.25 - 128.0
    rcs       = b7 * 0.5 - 64.0
    r_m       = math.sqrt(x_m ** 2 + y_m ** 2)
    angle_deg = math.degrees(math.atan2(x_m, y_m))

    node.publish_target(target_id, x_m, y_m, v_m_s, rcs, r_m, angle_deg)

def rx_thread(dev_type, dev_idx, chn_idx, node: RadarPublisherNode):
    global g_thd_run
    node.get_logger().info(f"Listening for RAW radar data on Channel {chn_idx}...")

    # FIX 1: Check rclpy.ok() to ensure the thread dies if ROS goes down
    while g_thd_run == 1 and rclpy.ok():
        time.sleep(0.01)
        count = lib.VCI_GetReceiveNum(dev_type, dev_idx, chn_idx)
        if count > 0:
            can    = (ZCAN_CAN_OBJ * count)()
            rcount = lib.VCI_Receive(dev_type, dev_idx, chn_idx, byref(can), count, 100)
            for i in range(rcount):
                if can[i].RemoteFlag == 0:
                    raw_payload = bytes(can[i].Data[:can[i].DataLen])
                    parse_and_publish(can[i].ID, raw_payload, node)

def main(args=None):
    global g_thd_run, lib
    g_thd_run = 1

    rclpy.init(args=args)
    node = RadarPublisherNode()

    gBaud   = 0x1C00       # 500 kbps
    DevType = USBCAN_II
    DevIdx  = 0

    ret = lib.VCI_OpenDevice(DevType, DevIdx, 0)
    if ret == 0:
        node.get_logger().error("Open device fail. Check USB connection and permissions.")
        if rclpy.ok():
            rclpy.shutdown()
        raise SystemExit(1)

    node.get_logger().info("Device opened successfully. Initializing CAN channels...")

    threads = []
    for i in range(MAX_CHANNELS):
        init_config             = ZCAN_CAN_INIT_CONFIG()
        init_config.AccCode     = 0
        init_config.AccMask     = 0xFFFFFFFF
        init_config.Reserved    = 0
        init_config.Filter      = 1
        init_config.Timing0     = gBaud & 0xFF
        init_config.Timing1     = (gBaud >> 8) & 0xFF
        init_config.Mode        = 0

        ret = lib.VCI_InitCAN(DevType, DevIdx, i, byref(init_config))
        if ret == 0:
            node.get_logger().warn(f"VCI_InitCAN failed on channel {i}")
            continue

        ret = lib.VCI_StartCAN(DevType, DevIdx, i)
        if ret == 0:
            node.get_logger().warn(f"VCI_StartCAN failed on channel {i}")
            continue

        t = threading.Thread(
            target=rx_thread,
            args=(DevType, DevIdx, i, node),
            daemon=True
        )
        threads.append(t)
        t.start()

    node.get_logger().info("Publishing SR73F Radar Data on /rawradar. Ctrl+C to stop...")

    # FIX 2: Fully restructured shutdown sequence
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("SIGINT received. Shutting down gracefully...")
    finally:
        # 1. Signal threads to stop reading from the USB adapter
        g_thd_run = 0

        # 2. Wait up to 2 seconds for threads to finish their current loop
        for t in threads:
            t.join(timeout=2.0)

        # 3. Safely reset and close the CAN hardware
        for i in range(MAX_CHANNELS):
            lib.VCI_ResetCAN(DevType, DevIdx, i)
        lib.VCI_CloseDevice(DevType, DevIdx)

        # 4. Log success *before* destroying the node
        node.get_logger().info("CAN Device closed and released gracefully.")

        # 5. Clean up ROS safely
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()