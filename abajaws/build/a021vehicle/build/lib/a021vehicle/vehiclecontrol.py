#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage
from std_msgs.msg import Float32


class ZoneStopAEBNode(Node):
    def __init__(self):
        super().__init__('zone_stop_aeb_node')

        # Control State Machine: 1 = CRUISE, -1 = BRAKING (for 6 seconds)
        self.state = 1 

        # Data Extraction Variables
        self.rel_dist = 100.0       # Closing Distance (X)
        self.Y = 0.0                # Lateral Offset (Y)
        self.data_received = False

        # Actuator command tracking states
        self.current_brake_val = 0.0
        self.current_throttle_val = 1.0

        # --- SAFETY THRESHOLDS ---
        self.brake_trigger_dist = 15.0 # Slam brakes immediately at this distance (15 meters)
        self.lane_width_half = 1.75    # Lane boundaries (-1.75m to 1.75m)
        
        # --- TIMING ---
        self.brake_start_time = None   # Will store the timestamp of when the brake is triggered

        # Subscribers & Publishers
        self.subscription = self.create_subscription(
            RadarMessage,
            '/radar_data',
            self.radar_callback,
            10
        )

        self.brake_publisher = self.create_publisher(Float32, '/brake_cmd', 10)
        self.throttle_publisher = self.create_publisher(Float32, '/throttle_cmd', 10)
        
        # 10Hz Control Loop Timer
        self.control_timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info("Zone-Based AEB initialized. Brake trigger set to 15.0m.")

    def radar_callback(self, msg: RadarMessage):
        """Extracts spatial data directly from the radar."""
        self.rel_dist = msg.x  # Closing Distance (X)
        self.Y = msg.y         # Lateral Offset (Y)
        self.data_received = True

    def control_loop(self):
        """Monitors the threshold and locks down vehicle actuators upon violation."""
        if not self.data_received:
            brake_msg = Float32()
            throttle_msg = Float32()

            brake_msg.data = 0.0
            throttle_msg.data = 1.0

            self.brake_publisher.publish(brake_msg)
            self.throttle_publisher.publish(throttle_msg)
            return

        # Check lane boundaries
        in_lane = (-self.lane_width_half < self.Y < self.lane_width_half)

        # --- STATE MACHINE LOGIC ---
        if self.state == 1:
            # TRIGGER CONDITION: If an object enters our lane and is closer than 15 meters
            if in_lane and (self.rel_dist <= self.brake_trigger_dist):
                self.state = -1
                self.current_brake_val = 1.0
                self.current_throttle_val = 0.0
                
                # Record the exact time the brake was triggered
                self.brake_start_time = self.get_clock().now()
                
                self.get_logger().error(
                    f"!!! EMERGENCY BRAKE !!! Target at {self.rel_dist:.2f}m. Locking vehicle down for 6 seconds."
                )
            else:
                # Normal Cruise State
                self.current_brake_val = 0.0
                self.current_throttle_val = 1.0

        elif self.state == -1:
            # CHECK TIMER: Calculate how many seconds have passed since brake triggered
            now = self.get_clock().now()
            elapsed_time = (now - self.brake_start_time).nanoseconds / 1e9

            if elapsed_time >= 10.0:
                # 6 seconds have passed, reset the system to CRUISE
                self.state = 1
                self.current_brake_val = 0.0
                self.current_throttle_val = 1.0
                self.data_received = False  # Force it to wait for fresh radar data
                
                self.get_logger().warn("AEB Reset: 6-second lock expired. Restarting normal operations.")
            else:
                # Still within the 6-second window: Keep brakes locked at 1.0
                self.current_brake_val = 1.0
                self.current_throttle_val = 0.0

        # --- PUBLISH Actuator COMMANDS ---
        brake_msg = Float32()
        throttle_msg = Float32()
        
        brake_msg.data = self.current_brake_val
        throttle_msg.data = self.current_throttle_val

        self.brake_publisher.publish(brake_msg)
        self.throttle_publisher.publish(throttle_msg)


def main(args=None):
    rclpy.init(args=args)
    node = ZoneStopAEBNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("AEB Node shutting down safely...")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
