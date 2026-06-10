# import threading
# import time
# import math
# from ctypes import *
# from datetime import datetime

# # Load the USBCAN library
# # lib = cdll.LoadLibrary("./libusbcan.so")
# # current_dir = os.path.dirname(os.path.abspath(__file__))

# # # 2. Check if the .so file is in a 'dependencies' subfolder (like when running in src/) 
# # #    or right next to the script (like when running in install/)
# # # if os.path.exists(os.path.join(current_dir, "dependencies", "libusbcan.so")):
# # #     lib_path = os.path.join(current_dir, "dependencies", "libusbcan.so")
# # # else:
# # #     lib_path = os.path.join(current_dir, "libusbcan.so")

# # # # 3. Load the library safely using its absolute path
# # # print(f"Loading driver library from: {lib_path}")
# # lib = cdll.LoadLibrary("./libusbcan.so")
# _here = os.path.dirname(os.path.abspath(__file__))
# lib = cdll.LoadLibrary(os.path.join(_here, "libusbcan.so"))
# USBCAN_I = c_uint32(3)    # USBCAN-I/I+
# USBCAN_II = c_uint32(4)   # USBCAN-II/II+
# MAX_CHANNELS = 2

# # Run flag
# g_thd_run = 1

# class ZCAN_CAN_INIT_CONFIG(Structure):
#     _fields_ = [
#         ("AccCode", c_int),
#         ("AccMask", c_int),
#         ("Reserved", c_int),
#         ("Filter", c_ubyte),
#         ("Timing0", c_ubyte),
#         ("Timing1", c_ubyte),
#         ("Mode", c_ubyte),
#     ]

# class ZCAN_CAN_OBJ(Structure):
#     _fields_ = [
#         ("ID", c_uint32),
#         ("TimeStamp", c_uint32),
#         ("TimeFlag", c_uint8),
#         ("SendType", c_byte),
#         ("RemoteFlag", c_byte),
#         ("ExternFlag", c_byte),
#         ("DataLen", c_byte),
#         ("Data", c_ubyte * 8),
#         ("Reserved", c_ubyte * 3),
#     ]


# def parse_and_print_sr73f_data(can_id, data_bytes):
#     """
#     Decode SR73F/MR72 payload and print raw output parameters as is.
#     No filtering or temporal tracking is applied.
#     """
#     if can_id != 0x60b:
#         return

#     if len(data_bytes) < 8:
#         return

#     b0, b1, b2, b3, b4, b5, b6, b7 = data_bytes

#     # Exact same decoding math from the original file
#     target_id = b0
#     y_m = (b1 * 32 + (b2 >> 3)) * 0.2 - 500.0
#     x_m = (((b2 & 0x07) * 256) + b3) * 0.2 - 204.6
#     v_m_s = (b4 * 4 + (b5 >> 6)) * 0.25 - 128.0
#     rcs = b7 * 0.5 - 64.0

#     r_m = math.sqrt(x_m ** 2 + y_m ** 2)
#     angle_deg = math.degrees(math.atan2(x_m, y_m))
    
#     now_str = datetime.now().strftime("%Y_%m_%d %H:%M:%S.%f")[:-3]

#     # Display decoded data consistently
#     print(
#         f"Time: {now_str}, ID: {target_id}, RCS: {rcs:.1f}, "
#         f"X: {x_m:.2f}, Y: {y_m:.2f}, V: {v_m_s:.2f}, R: {r_m:.2f}, Angle: {angle_deg:.2f}°"
#     )


# def rx_thread(dev_type, dev_idx, chn_idx):
#     global g_thd_run
#     print(f"Listening for RAW radar data on Channel {chn_idx}...")

#     while g_thd_run == 1:
#         time.sleep(0.01)
#         count = lib.VCI_GetReceiveNum(dev_type, dev_idx, chn_idx)
#         if count > 0:
#             can = (ZCAN_CAN_OBJ * count)()
#             rcount = lib.VCI_Receive(dev_type, dev_idx, chn_idx, byref(can), count, 100)

#             for i in range(rcount):
#                 if can[i].RemoteFlag == 0:
#                     raw_payload = bytes(can[i].Data[:can[i].DataLen])
#                     parse_and_print_sr73f_data(can[i].ID, raw_payload)


# def wait_for_exit():
#     global g_thd_run
#     input()
#     g_thd_run = 0


# if __name__ == "__main__":
#     threads = []

#     gBaud = 0x1C00       # 500 kbps
#     DevType = USBCAN_II
#     DevIdx = 0

#     ret = lib.VCI_OpenDevice(DevType, DevIdx, 0)
#     if ret == 0:
#         print("Open device fail. Please check USB connection and permissions.")
#         raise SystemExit(1)

#     print("Device opened successfully. Initializing CAN channels...")

#     for i in range(MAX_CHANNELS):
#         init_config = ZCAN_CAN_INIT_CONFIG()
#         init_config.AccCode = 0
#         init_config.AccMask = 0xFFFFFFFF
#         init_config.Reserved = 0
#         init_config.Filter = 1
#         init_config.Timing0 = gBaud & 0xFF
#         init_config.Timing1 = (gBaud >> 8) & 0xFF
#         init_config.Mode = 0

#         ret = lib.VCI_InitCAN(DevType, DevIdx, i, byref(init_config))
#         if ret == 0:
#             print(f"VCI_InitCAN failed on channel {i}")
#             continue

#         ret = lib.VCI_StartCAN(DevType, DevIdx, i)
#         if ret == 0:
#             print(f"VCI_StartCAN failed on channel {i}")
#             continue

#         t = threading.Thread(target=rx_thread, args=(DevType, DevIdx, i), daemon=True)
#         threads.append(t)
#         t.start()

#     exit_thread = threading.Thread(target=wait_for_exit, daemon=True)
#     exit_thread.start()

#     print("Listening for SR73F Radar Data. Press ENTER to stop...")

#     # Replaces the run_plots() loop to keep the main thread alive 
#     # until the user presses ENTER in the exit_thread.
#     while g_thd_run == 1:
#         time.sleep(0.1)

#     print("Stopping threads and shutting down device...")

#     for t in threads:
#         t.join(timeout=1.0)

#     for i in range(MAX_CHANNELS):
#         lib.VCI_ResetCAN(DevType, DevIdx, i)

#     lib.VCI_CloseDevice(DevType, DevIdx)
#     del lib

#     print("Device closed.")


###################################################
#WORKING SCRIPT
###################################################


# import os
# import threading
# import time
# import math
# from ctypes import *
# from datetime import datetime

# # Load the USBCAN library using a path relative to this file
# _here = os.path.dirname(os.path.abspath(__file__))
# lib = cdll.LoadLibrary(os.path.join(_here, "libusbcan.so"))

# USBCAN_I = c_uint32(3)    # USBCAN-I/I+
# USBCAN_II = c_uint32(4)   # USBCAN-II/II+
# MAX_CHANNELS = 2

# # Run flag
# g_thd_run = 1


# class ZCAN_CAN_INIT_CONFIG(Structure):
#     _fields_ = [
#         ("AccCode", c_int),
#         ("AccMask", c_int),
#         ("Reserved", c_int),
#         ("Filter", c_ubyte),
#         ("Timing0", c_ubyte),
#         ("Timing1", c_ubyte),
#         ("Mode", c_ubyte),
#     ]


# class ZCAN_CAN_OBJ(Structure):
#     _fields_ = [
#         ("ID", c_uint32),
#         ("TimeStamp", c_uint32),
#         ("TimeFlag", c_uint8),
#         ("SendType", c_byte),
#         ("RemoteFlag", c_byte),
#         ("ExternFlag", c_byte),
#         ("DataLen", c_byte),
#         ("Data", c_ubyte * 8),
#         ("Reserved", c_ubyte * 3),
#     ]


# def parse_and_print_sr73f_data(can_id, data_bytes):
#     """
#     Decode SR73F/MR72 payload and print raw output parameters as is.
#     No filtering or temporal tracking is applied.
#     """
#     if can_id != 0x60b:
#         return

#     if len(data_bytes) < 8:
#         return

#     b0, b1, b2, b3, b4, b5, b6, b7 = data_bytes

#     target_id = b0
#     y_m = (b1 * 32 + (b2 >> 3)) * 0.2 - 500.0
#     x_m = (((b2 & 0x07) * 256) + b3) * 0.2 - 204.6
#     v_m_s = (b4 * 4 + (b5 >> 6)) * 0.25 - 128.0
#     rcs = b7 * 0.5 - 64.0

#     r_m = math.sqrt(x_m ** 2 + y_m ** 2)
#     angle_deg = math.degrees(math.atan2(x_m, y_m))

#     now_str = datetime.now().strftime("%Y_%m_%d %H:%M:%S.%f")[:-3]

#     print(
#         f"Time: {now_str}, ID: {target_id}, RCS: {rcs:.1f}, "
#         f"X: {x_m:.2f}, Y: {y_m:.2f}, V: {v_m_s:.2f}, R: {r_m:.2f}, Angle: {angle_deg:.2f}°"
#     )


# def rx_thread(dev_type, dev_idx, chn_idx):
#     global g_thd_run
#     print(f"Listening for RAW radar data on Channel {chn_idx}...")

#     while g_thd_run == 1:
#         time.sleep(0.01)
#         count = lib.VCI_GetReceiveNum(dev_type, dev_idx, chn_idx)
#         if count > 0:
#             can = (ZCAN_CAN_OBJ * count)()
#             rcount = lib.VCI_Receive(dev_type, dev_idx, chn_idx, byref(can), count, 100)

#             for i in range(rcount):
#                 if can[i].RemoteFlag == 0:
#                     raw_payload = bytes(can[i].Data[:can[i].DataLen])
#                     parse_and_print_sr73f_data(can[i].ID, raw_payload)


# def wait_for_exit():
#     global g_thd_run
#     input()
#     g_thd_run = 0


# def main():
    
#     global g_thd_run, lib
#     g_thd_run = 1
#     threads = []

#     gBaud = 0x1C00       # 500 kbps
#     DevType = USBCAN_II
#     DevIdx = 0

#     ret = lib.VCI_OpenDevice(DevType, DevIdx, 0)
#     if ret == 0:
#         print("Open device fail. Please check USB connection and permissions.")
#         raise SystemExit(1)

#     print("Device opened successfully. Initializing CAN channels...")

#     for i in range(MAX_CHANNELS):
#         init_config = ZCAN_CAN_INIT_CONFIG()
#         init_config.AccCode = 0
#         init_config.AccMask = 0xFFFFFFFF
#         init_config.Reserved = 0
#         init_config.Filter = 1
#         init_config.Timing0 = gBaud & 0xFF
#         init_config.Timing1 = (gBaud >> 8) & 0xFF
#         init_config.Mode = 0

#         ret = lib.VCI_InitCAN(DevType, DevIdx, i, byref(init_config))
#         if ret == 0:
#             print(f"VCI_InitCAN failed on channel {i}")
#             continue

#         ret = lib.VCI_StartCAN(DevType, DevIdx, i)
#         if ret == 0:
#             print(f"VCI_StartCAN failed on channel {i}")
#             continue

#         t = threading.Thread(target=rx_thread, args=(DevType, DevIdx, i), daemon=True)
#         threads.append(t)
#         t.start()

#     exit_thread = threading.Thread(target=wait_for_exit, daemon=True)
#     exit_thread.start()

#     print("Listening for SR73F Radar Data. Press ENTER to stop...")

#     while g_thd_run == 1:
#         time.sleep(0.1)

#     print("Stopping threads and shutting down device...")

#     for t in threads:
#         t.join(timeout=1.0)

#     for i in range(MAX_CHANNELS):
#         lib.VCI_ResetCAN(DevType, DevIdx, i)

#     lib.VCI_CloseDevice(DevType, DevIdx)
#     del lib

#     print("Device closed.")


# if __name__ == "__main__":
#     main()
    
##################################
# RECIVER ADDITION
##################################

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
        self.get_logger().info(
            f"ID: {target_id:3d} | "
            f"Pos: ({x_m:6.2f}m, {y_m:6.2f}m) | "
            f"Vel: {v_m_s:6.2f}m/s | "
            f"RCS: {rcs:5.1f}dBsm | "
            f"Range: {r_m:6.2f}m | "
            f"Angle: {angle_deg:6.2f}°"
        )


def parse_and_publish(can_id, data_bytes, node: RadarPublisherNode):
    if can_id != 0x60b:
        return
    if len(data_bytes) < 8:
        return

    b0, b1, b2, b3, b4, b5, b6, b7 = data_bytes

    target_id = b0
    y_m       = (b1 * 32 + (b2 >> 3)) * 0.2 - 500.0
    x_m       = (((b2 & 0x07) * 256) + b3) * 0.2 - 204.6
    v_m_s     = (b4 * 4 + (b5 >> 6)) * 0.25 - 128.0
    rcs       = b7 * 0.5 - 64.0
    r_m       = math.sqrt(x_m ** 2 + y_m ** 2)
    angle_deg = math.degrees(math.atan2(x_m, y_m))

    node.publish_target(target_id, x_m, y_m, v_m_s, rcs, r_m, angle_deg)


def rx_thread(dev_type, dev_idx, chn_idx, node: RadarPublisherNode):
    global g_thd_run
    node.get_logger().info(f"Listening for RAW radar data on Channel {chn_idx}...")

    while g_thd_run == 1:
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

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down...")
    finally:
        g_thd_run = 0

        for t in threads:
            t.join(timeout=1.0)

        for i in range(MAX_CHANNELS):
            lib.VCI_ResetCAN(DevType, DevIdx, i)

        lib.VCI_CloseDevice(DevType, DevIdx)
        node.destroy_node()
        rclpy.shutdown()
        node.get_logger().info("Device closed.")


if __name__ == "__main__":
    main()