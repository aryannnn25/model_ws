#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage
from std_msgs.msg import Int32, Float32


class RadarReceiverNode(Node):
    def __init__(self):
        super().__init__('radar_receiver_node')

        self.subscription = self.create_subscription(
            RadarMessage,
            '/radar_data',
            self.listener_callback_radar,
            10  # QoS History depth
        )
        self.subscription  # Prevent unused variable warning

        self.phase_subscription = self.create_subscription(
            Int32,
            '/phase_id',
            self.listener_callback_phase,
            10  # QoS History depth
        )
        self.phase_subscription  # Prevent unused variable warning

        self.brake_publisher = self.create_publisher(
            Float32,
            '/brake_cmd',
            10
        )

        self.get_logger().info("Listening on /radar_data and...")

    def listener_callback_radar(self, msg: RadarMessage):
        """
        Callback function executed every time a new radar tracking frame 
        arrives from the publisher node.
        """
        # Extract the fields safely using native attributes
        tid   = msg.target_id
        x     = msg.x
        y     = msg.y
        v     = msg.v
        rcs   = msg.rcs
        r     = msg.r
        angle = msg.angle

        # Print the data to the console
        self.get_logger().info(
            f"[TARGET INCOMING] ID: {tid:3d} | "
            f"Pos: ({x:6.2f}m, {y:6.2f}m) | "
            f"Vel: {v:6.2f}m/s | "
            f"RCS: {rcs:5.1f}dBsm | "
            f"Range: {r:6.2f}m | "
            f"Angle: {angle:6.2f}°"
        )

    def listener_callback_phase(self, msg: Int32):
        """
        Callback function executed every time a phase_id message arrives.
        Triggers braking logic when phase_id is -1.
        """
        phase = msg.data
        if phase == -1:
            self.apply_braking()

    def apply_braking(self):
        """
        Braking logic — publishes a hardcoded brake command of 1.0
        to /brake_cmd when phase_id is -1.
        """
        brake_msg = Float32()
        brake_msg.data = 1.0
        self.brake_publisher.publish(brake_msg)
        self.get_logger().warn(
            "BRAKING: Phase ID -1 received — publishing brake command 1.0 to /brake_cmd"
        )


def main(args=None):
    rclpy.init(args=args)
    node = RadarReceiverNode()

    try:
        # Keep the node running, waiting for incoming messages
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Receiver node shutting down gracefully...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()