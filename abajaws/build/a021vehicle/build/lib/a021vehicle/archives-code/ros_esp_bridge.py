#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import can
import struct
import time
import threading
import csv
from datetime import datetime

CAN_ID_JETSON_CMD = 0x210
CAN_ID_ESP32_TEL  = 0x160
CAN_ID_ESP32_STAT = 0x161
CAN_ID_ESP32_RPM  = 0x162

class CANBrakeBridgeNode(Node):
    def __init__(self):
        super().__init__('can_brake_bridge')
        
        self.brake_cmd = 0.0
        self.latest_speed_kmh = 0.0
        self.latest_accel_ms2 = 0.0
        self.latest_brake_state = 0
        self.latest_control_mode = 0
        self.latest_raw_rpm = 0.0
        self.latest_filt_rpm = 0.0
        self.rx_count = 0
        self.tx_count = 0
        
        # ── State Machine ───────────────────────────────────────────
        self.aeb_state = 'RETRACT'
        self.aeb_timer = 0.0
        self.sequence_active = False
        self.prev_brake_cmd = 0.0
        
        # ── CSV Logging Initialization ──────────────────────────────
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"telemetry_{timestamp_str}.csv"
        try:
            self.csv_file = open(self.csv_filename, mode='w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            self.csv_writer.writerow([
                "Timestamp", 
                "Speed_kmh", 
                "Accel_ms2", 
                "Raw_RPM", 
                "Filtered_RPM", 
                "Brake_State", 
                "Control_Mode"
            ])
            self.get_logger().info(f"Logging telemetry to CSV file: {self.csv_filename}")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize CSV logging: {e}")
            self.csv_file = None
            
        # ── ROS 2 Subscribers ───────────────────────────────────────
        self.subscription = self.create_subscription(
            Float32,
            '/brake_cmd',
            self.brake_callback,
            10
        )
        
        # ── CAN Initialization ──────────────────────────────────────
        try:
            self.bus = can.interface.Bus(channel='can1', interface='socketcan', bitrate=1000000)
            self.get_logger().info("Successfully connected to CAN bus (can1) at 1 Mbps.")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to CAN: {e}. Did you run 'sudo ip link set can1 up'?")
            raise RuntimeError("CAN init failed")
            
        self.running = True
        self.rx_thread = threading.Thread(target=self.can_rx_loop, daemon=True)
        self.rx_thread.start()
        
        # ── Timers ──────────────────────────────────────────────────
        # 100 Hz CAN Transmit Loop (0.01 seconds)
        self.tx_timer = self.create_timer(0.01, self.can_tx_loop)
        
        # 2 Hz Dashboard Print Loop (0.5 seconds)
        self.dash_timer = self.create_timer(0.5, self.dashboard_loop)
        
        print("\n" + "=" * 60)
        print("  JETSON AEB LONGITUDINAL CONTROLLER (CAN BUS 1Mbps)")
        print("=" * 60 + "\n")

    def brake_callback(self, msg: Float32):
        """Receives incoming brake commands from the vehiclecontrol node."""
        new_brake = max(0.0, min(1.0, float(msg.data)))
        if new_brake > 0.5 and self.brake_cmd <= 0.5:
             print(f"\n[AEB TRIGGERED] Brake command updated to 1 (EXTEND SEQUENCE)")
        self.brake_cmd = new_brake

    def can_rx_loop(self):
        """Background thread to listen to ESP32 CAN telemetry."""
        while self.running:
            try:
                msg = self.bus.recv(timeout=0.1)
                if msg is None: continue
                
                self.rx_count += 1
                
                if msg.arbitration_id == CAN_ID_ESP32_TEL and msg.dlc >= 8:
                    # Unpack 2 floats (speed_kmh, accel_ms2)
                    speed, accel = struct.unpack('<ff', msg.data[:8])
                    self.latest_speed_kmh = speed
                    self.latest_accel_ms2 = accel
                    
                    # Log telemetry to CSV
                    self.log_to_csv()
                    
                elif msg.arbitration_id == CAN_ID_ESP32_RPM and msg.dlc >= 8:
                    # Unpack 2 floats (raw_rpm, filtered_rpm)
                    raw_rpm, filt_rpm = struct.unpack('<ff', msg.data[:8])
                    self.latest_raw_rpm = raw_rpm
                    self.latest_filt_rpm = filt_rpm
                    
                elif msg.arbitration_id == CAN_ID_ESP32_STAT and msg.dlc >= 2:
                    # Unpack 2 bytes (brake_state, control_mode)
                    self.latest_brake_state = msg.data[0]
                    self.latest_control_mode = msg.data[1]
                    
            except Exception:
                pass

    def log_to_csv(self):
        """Logs current telemetry snapshot to CSV file."""
        if self.csv_file:
            try:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                self.csv_writer.writerow([
                    now_str,
                    f"{self.latest_speed_kmh:.2f}",
                    f"{self.latest_accel_ms2:.2f}",
                    f"{self.latest_raw_rpm:.2f}",
                    f"{self.latest_filt_rpm:.2f}",
                    self.latest_brake_state,
                    self.latest_control_mode
                ])
                self.csv_file.flush()
            except Exception:
                pass

    def can_tx_loop(self):
        """Executes at 100Hz: Runs the state machine and sends the command byte to the ESP32."""
        now = time.time()
        
        # Detect rising edge of brake command
        if self.brake_cmd > 0.5 and self.prev_brake_cmd <= 0.5:
            if not self.sequence_active:
                self.sequence_active = True
                self.aeb_state = 'EXTEND'
                self.aeb_timer = now
                print(f"\n[AEB TRIGGERED] Brake command active. Starting sequence: EXTEND (5s)")
        
        self.prev_brake_cmd = self.brake_cmd
        
        # Handle state transitions
        if self.sequence_active:
            if self.aeb_state == 'EXTEND':
                if now - self.aeb_timer >= 5.0:
                    self.aeb_state = 'HOLD'
                    self.aeb_timer = now
                    print(f"\n[AEB SEQUENCE] Transition to: HOLD (3s)")
            elif self.aeb_state == 'HOLD':
                if now - self.aeb_timer >= 3.0:
                    self.aeb_state = 'RETRACT'
                    self.aeb_timer = now
                    self.sequence_active = False
                    print(f"\n[AEB SEQUENCE] Transition to: RETRACT (brakes released)")
        else:
            self.aeb_state = 'RETRACT'
            
        # Map state to cmd_byte (0=HOLD, 1=EXTEND, 2=RETRACT)
        if self.aeb_state == 'EXTEND':
            cmd_byte = 1
        elif self.aeb_state == 'RETRACT':
            cmd_byte = 2
        else: # HOLD
            cmd_byte = 0
            
        msg = can.Message(arbitration_id=CAN_ID_JETSON_CMD, data=[cmd_byte], is_extended_id=False)
        try:
            self.bus.send(msg)
            self.tx_count += 1
        except Exception:
            pass

    def dashboard_loop(self):
        """Executes at 2Hz: Prints the live vehicle data dashboard."""
        state_strs = ["HOLD", "EXTEND", "RETRACT"]
        mode_strs = ["JETSON_CAN", "RC_FALLBACK", "FAILSAFE"]
        
        b_idx = min(2, self.latest_brake_state)
        m_idx = min(2, self.latest_control_mode)
        
        dash = (
            f"\r  SPD:{self.latest_speed_kmh:5.1f} km/h | "
            f"ACC:{self.latest_accel_ms2:6.2f} m/s^2 | "
            f"JETSON_CMD:{self.aeb_state:7s} | "
            f"ACT_STATE:{state_strs[b_idx]} | "
            f"CTRL_MODE:{mode_strs[m_idx]} | "
            f"RX:{self.rx_count} TX:{self.tx_count}"
        )
        print(dash + "   ", end="", flush=True)

    def destroy_node(self):
        """Shutdown hook to safely kill the throttle/brakes on the ESP32."""
        print("\n\n[SHUTDOWN] Node killed. Sending idle (0) to ESP32...")
        self.running = False
        try:
            # Send 3 idle frames to ensure ESP32 receives it
            for _ in range(3):
                msg = can.Message(arbitration_id=CAN_ID_JETSON_CMD, data=[0], is_extended_id=False)
                self.bus.send(msg)
                time.sleep(0.01)
            self.bus.shutdown()
        except:
            pass
            
        # Close CSV file
        if hasattr(self, 'csv_file') and self.csv_file:
            try:
                self.csv_file.close()
                print(f"[SHUTDOWN] Closed telemetry CSV log file: {self.csv_filename}")
            except Exception:
                pass
                
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CANBrakeBridgeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

