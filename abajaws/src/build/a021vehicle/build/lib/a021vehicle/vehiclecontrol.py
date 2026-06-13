safe

#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage
from std_msgs.msg import Float32


class ZoneStopAEBNode(Node):
    def __init__(self):
        super().__init__('zone_stop_aeb_node')

        # Control State Machine: 1 = CRUISE, -1 = PERMANENTLY STOPPED
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
        self.get_logger().info("Zone-Based AEB initialized. Brake trigger set to 12.0m.")
    def radar_callback(self, msg: RadarMessage):
        """Extracts spatial data directly from the radar."""
        self.rel_dist = msg.x  # Closing Distance (X)
        self.Y = msg.y         # Lateral Offset (Y)
        self.data_received = True
    def control_loop(self):
        """Monitors the 12m threshold and locks down vehicle actuators upon violation."""
        if not self.data_received:
            # return
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
            # TRIGGER CONDITION: If an object enters our lane and is closer than 12 meters
            # Note: Using '<= 12.0' ensures that if an object appears anywhere between 12m and 6m (or closer), it triggers.
            if in_lane and (self.rel_dist <= self.brake_trigger_dist):
                self.state = -1
                self.current_brake_val = 1.0
                self.current_throttle_val = 0.0
                self.get_logger().error(
                    f"!!! EMERGENCY BRAKE !!! Target at {self.rel_dist:.2f}m. Locking vehicle down."
                )
            else:
                # Normal Cruise State
                self.current_brake_val = 0.0
                self.current_throttle_val = 1.0

        elif self.state == -1:
            # PERMANENT LATCH: Bypasses all radar data. Brakes stuck at 1.0, Throttle stuck at 0.0.
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
        rclpy.shutdown()


if __name__ == '__main__':
    main()
