#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

import spidev
import struct
import time

# =====================================================
# SPI PROTOCOL (Must match ESP1 firmware exactly)
# =====================================================
FRAME_FMT_LONG_REQ  = "<IfffBB"      # jetson_time_ms, throttle_cmd, brake_cmd, reserved, hb, flags
FRAME_FMT_LONG_RESP = "<BBHIfffffffHHH"  # node_id, msg_type, seq, time, speed, dist, accel, thr_cmd, thr_fb, brk_cmd, brk_fb, mode, fault, crc

REQ_SIZE  = struct.calcsize(FRAME_FMT_LONG_REQ)    # 18 bytes
RESP_SIZE = struct.calcsize(FRAME_FMT_LONG_RESP)   # 44 bytes
DMA_SIZE  = 44  # ESP32 DMA buffer size

LONG_FIELDS = [
    "node_id", "msg_type", "seq", "jetson_time_ms",
    "veh_speed_mps", "distance_m", "accel_mps2",
    "throttle_cmd_pct", "throttle_fb_pct",
    "brake_cmd_pct", "brake_fb_pct",
    "mode_flags", "fault_flags", "crc",
]

# =====================================================
# SPI SETTINGS
# =====================================================
SPI_BUS      = 1
SPI_DEV      = 0
SPI_SPEED_HZ = 8_000_000
SPI_MODE     = 0

# =====================================================
# UTILITY FUNCTIONS
# =====================================================
def crc16_ccitt(data: bytes) -> int:
    """CRC-16-CCITT (poly 0x1021, init 0xFFFF)."""
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
    return crc & 0xFFFF

def validate_crc(raw: bytes) -> bool:
    """Validate CRC on raw ESP1 response frame."""
    if len(raw) < 3:
        return False
    payload = raw[:-2]
    rx_crc, = struct.unpack_from("<H", raw, len(raw) - 2)
    return crc16_ccitt(payload) == rx_crc

def decode_long(raw: bytes) -> dict | None:
    """Decode longitudinal response frame."""
    if len(raw) < RESP_SIZE:
        return None
    try:
        return dict(zip(LONG_FIELDS, struct.unpack(FRAME_FMT_LONG_RESP, raw[:RESP_SIZE])))
    except Exception:
        return None

def decode_state(flags: int) -> str:
    """Decode ESP1 mode_flags into human-readable state."""
    if flags & 0x0001: return "HOMING"
    if flags & 0x0004: return "BRAKING"
    if flags & 0x0008: return "DONE"
    if flags & 0x0002: return "SPEED_CTRL"
    return "UNKNOWN"


# =====================================================
# ROS 2 NODE
# =====================================================
class AEBSPIBridgeNode(Node):
    def __init__(self):
        super().__init__('spi_brake_bridge')

        # ── Node State ──────────────────────────────────────────────
        self.brake_cmd = 0.0
        self.heartbeat = 0
        self.total_cycles = 0
        self.crc_ok_count = 0
        self.crc_fail_count = 0
        self.last_dash_t = time.monotonic()
        self.latest_frame = None

        # ── ROS 2 Subscribers ───────────────────────────────────────
        self.subscription = self.create_subscription(
            Float32,
            '/brake_cmd',
            self.brake_callback,
            10
        )

        # ── SPI Initialization ──────────────────────────────────────
        self.spi = spidev.SpiDev()
        try:
            self.spi.open(SPI_BUS, SPI_DEV)
            self.spi.max_speed_hz = SPI_SPEED_HZ
            self.spi.mode = SPI_MODE
            self.get_logger().info(f"SPI initialized on Bus {SPI_BUS}, Dev {SPI_DEV} at {SPI_SPEED_HZ/1e6:.1f}MHz.")
        except Exception as e:
            self.get_logger().error(f"Failed to open SPI port: {e}")
            raise

        # ── Timers (Replacing the while loop) ───────────────────────
        # 100 Hz SPI Exchange Loop (0.01 seconds)
        self.spi_timer = self.create_timer(0.01, self.spi_loop)
        
        # 2 Hz Dashboard Print Loop (0.5 seconds)
        self.dash_timer = self.create_timer(0.5, self.dashboard_loop)

        self.get_logger().info("Integrated AEB SPI Bridge running! Listening to /brake_cmd...")
        print("\n" + "=" * 50)
        print("  JETSON AEB LONGITUDINAL CONTROLLER (ROS 2)")
        print("=" * 50 + "\n")

    def brake_callback(self, msg: Float32):
        """Receives incoming brake commands from the vehiclecontrol node."""
        new_brake = max(0.0, min(1.0, float(msg.data)))
        # Only log if there's a significant change to prevent spamming the dashboard
        if abs(new_brake - self.brake_cmd) > 0.05 and new_brake > 0.1:
             print(f"\n[AEB TRIGGERED] Brake command updated to: {new_brake:.2f}")
        self.brake_cmd = new_brake

    def spi_exchange(self, payload: bytes) -> bytes:
        """Send SPI request, receive response, handling DMA padding."""
        pad_len = max(0, (DMA_SIZE + 4) - len(payload))
        tx = list(payload + bytes(pad_len))
        rx = self.spi.xfer2(tx)
        return bytes(rx[:RESP_SIZE])

    def spi_loop(self):
        """Executes at 100Hz: Packs data, sends SPI, decodes response."""
        self.total_cycles += 1
        t_ms = int(time.time() * 1000) & 0xFFFFFFFF
        hb = self.heartbeat & 0xFF
        self.heartbeat += 1

        # Build Request (18 bytes)
        req = struct.pack(FRAME_FMT_LONG_REQ,
                          t_ms,            # jetson_time_ms
                          0.0,             # throttle_cmd_pct (ESP1 PID handles this)
                          self.brake_cmd,  # brake_cmd_pct (From ROS /brake_cmd)
                          0.0,             # reserved
                          hb,              # heartbeat
                          0x00)            # req_flags

        # Execute transaction
        try:
            raw = self.spi_exchange(req)
            self.latest_frame = decode_long(raw)

            if self.latest_frame and validate_crc(raw):
                self.crc_ok_count += 1
            else:
                self.crc_fail_count += 1
                self.latest_frame = None
        except Exception as e:
            self.get_logger().error(f"SPI Error during exchange: {e}")

    def dashboard_loop(self):
        """Executes at 2Hz: Prints the live vehicle data dashboard."""
        if self.latest_frame:
            spd_kmh  = self.latest_frame["veh_speed_mps"] * 3.6
            thr_cmd  = self.latest_frame["throttle_cmd_pct"]
            thr_fb   = self.latest_frame["throttle_fb_pct"]
            brk_fb   = self.latest_frame["brake_fb_pct"]
            mode     = int(self.latest_frame["mode_flags"]) & 0xFFFF
            state_str = decode_state(mode)
            aeb_flag = " [AEB]" if mode & 0x0100 else ""
            dist_m   = self.latest_frame["distance_m"]

            dash = (
                f"\r  SPD:{spd_kmh:5.1f} km/h | "
                f"THR:{thr_cmd:4.1f}% (fb:{thr_fb:4.1f}%) | "
                f"BRK_CMD:{self.brake_cmd:.2f} fb:{brk_fb:4.1f}% | "
                f"DIST:{dist_m:6.1f}m | "
                f"STATE:{state_str}{aeb_flag} | "
                f"CRC:{self.crc_ok_count}/{self.total_cycles}"
            )
            print(dash + "   ", end="", flush=True)
        else:
            print(f"\r  [NO VALID FRAME] CRC ok:{self.crc_ok_count} fail:{self.crc_fail_count}   ",
                  end="", flush=True)

    def destroy_node(self):
        """Shutdown hook to safely kill the throttle/brakes on the ESP32."""
        print("\n\n[SHUTDOWN] Node killed. Sending idle + stop to ESP32...")
        # Send 3 idle frames to ensure ESP1 receives it before SPI closes
        for _ in range(3):
            t_ms = int(time.time() * 1000) & 0xFFFFFFFF
            req = struct.pack(FRAME_FMT_LONG_REQ, t_ms, 0.0, 0.0, 0.0, 0, 0x00)
            try:
                self.spi_exchange(req)
            except:
                pass
            time.sleep(0.01)
            
        self.spi.close()
        print(f"[STATS] Total cycles: {self.total_cycles}")
        print(f"[STATS] CRC ok: {self.crc_ok_count} | CRC fail: {self.crc_fail_count}")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = AEBSPIBridgeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()