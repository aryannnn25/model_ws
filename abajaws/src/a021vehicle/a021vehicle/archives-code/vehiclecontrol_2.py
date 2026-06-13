#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from radar_interfaces.msg import RadarMessage
from std_msgs.msg import Int32, Float32


class RadarReceiverNode(Node):
    def __init__(self):
        super().__init__('radar_receiver_node')

        # Internal tracking state for continuous publishing
        self.current_brake_val = 0.0

        self.subscription = self.create_subscription(
            RadarMessage,
            '/radar_data',
            self.listener_callback_radar,
            10
        )

        # self.phase_subscription = self.create_subscription(
        #     Int32,
        #     '/phase_id',
        #     self.listener_callback_phase,
        #     10
        # )

        self.brake_publisher = self.create_publisher(
            Float32,
            '/brake_cmd',
            10
        )

        # Timer running at 10Hz to continuously broadcast brake commands
        self.brake_timer = self.create_timer(0.1, self.publish_brake_continuous)

        self.get_logger().info("Vehicle Control Node started. Continuous 0.0 command active.")

    def publish_brake_continuous(self):
        """Timer callback that continuously publishes current brake command at 10Hz"""
        brake_msg = Float32()
        brake_msg.data = self.current_brake_val
        self.brake_publisher.publish(brake_msg)
        
        # Optional tracing to keep eyes on the output state
        if self.current_brake_val == 1.0:
            self.get_logger().warn("BRAKING ACTIVE: Continuously publishing 1.0")

    def listener_callback_radar(self, msg: RadarMessage):
        tid   = msg.target_id
        x     = msg.x
        y     = msg.y
        v     = msg.v
        rcs   = msg.rcs
        r     = msg.r
        angle = msg.angle

        self.get_logger().info(
            f"[TARGET INCOMING] ID: {tid:3d} | "
            f"Pos: ({x:6.2f}m, {y:6.2f}m) | "
            f"Vel: {v:6.2f}m/s | "
            f"Range: {r:6.2f}m"
        )

    # def listener_callback_phase(self, msg: Int32):
    #     """Updates internal target state when phase messages change"""
    #     phase = msg.data
    #     if phase == -1:
    #         if self.current_brake_val != 1.0:
    #             self.get_logger().error("Phase -1 received! Overriding brake value to 1.0")
    #         self.current_brake_val = 1.0
    #     else:
    #         self.current_brake_val = 0.0


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