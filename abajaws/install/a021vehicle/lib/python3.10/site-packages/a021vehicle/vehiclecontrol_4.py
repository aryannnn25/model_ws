#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage
from std_msgs.msg import Float32


class RadarReceiverNode(Node):
    def __init__(self):
        super().__init__('radar_receiver_node')

        # Internal tracking state
        self.current_brake_val = 0.0
        self.tracked_x = float('inf')
        self.tracked_y = 0.0

        self.subscription = self.create_subscription(
            RadarMessage,
            '/radar_data',
            self.listener_callback_radar,
            10
        )

        self.brake_publisher = self.create_publisher(
            Float32,
            '/brake_cmd',
            10
        )

        # Timer running at 10Hz to continuously broadcast brake commands
        self.brake_timer = self.create_timer(0.1, self.publish_brake_continuous)

        self.get_logger().info("Vehicle Control Node started. Evaluating braking conditions...")

    def listener_callback_radar(self, msg: RadarMessage):
        """Main callback: No longer prints raw data, delegates logic to distinct functions."""
        self.update_target_state(msg.x, msg.y)
        self.evaluate_brake_condition()

    def update_target_state(self, x: float, y: float):
        """Updates the internal position state using the incoming radar data."""
        self.tracked_x = x
        self.tracked_y = y

    def evaluate_brake_condition(self):
        """Evaluates whether the tracked target falls within the critical braking zone."""
        if self.is_in_stopping_zone(self.tracked_x, self.tracked_y):
            self.current_brake_val = 1.0
        else:
            self.current_brake_val = 0.0

    def is_in_stopping_zone(self, x: float, y: float) -> bool:
        """Returns True if X is under 6m and Y is between -1.7m and 1.7m."""
        return (x < 6.0) and (-1.7 <= y <= 1.7)

    def publish_brake_continuous(self):
        """
        Timer callback that publishes at 10Hz. 
        If radar data becomes unavailable, this naturally carries 
        and publishes the last calculated brake command state.
        """
        brake_msg = Float32()
        brake_msg.data = self.current_brake_val
        self.brake_publisher.publish(brake_msg)
        
        # Optional logging only when actively braking to keep the terminal clean
        if self.current_brake_val == 1.0:
            self.get_logger().warn(f"EMERGENCY BRAKE: Target detected at X: {self.tracked_x:.2f}m")

def main(args=None):
    rclpy.init(args=args)
    node = RadarReceiverNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Receiver node shutting down gracefully...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()