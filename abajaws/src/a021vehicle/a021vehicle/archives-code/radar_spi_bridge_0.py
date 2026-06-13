#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import spidev
import struct


class SPIBridgeNode(Node):
    def __init__(self):
        super().__init__('spi_brake_bridge')

        # Subscribe to the brake command from your receiver node
        self.subscription = self.create_subscription(
            Float32,
            '/brake_cmd',
            self.brake_callback,
            10
        )

        # ─── SPI Configuration ─────────────────────────────────────────────
        self.spi = spidev.SpiDev()
        
        # Typically Jetson uses Bus 0, Device 0 (or Bus 1, Device 0)
        self.spi_bus = 0
        self.spi_device = 0
        
        try:
            self.spi.open(self.spi_bus, self.spi_device)
            # ESP32/ESP8266 can easily handle 1MHz - 5MHz. We'll set 1MHz.
            self.spi.max_speed_hz = 1000000
            # SPI Mode 0 (CPOL=0, CPHA=0) is standard for ESP devices
            self.spi.mode = 0
            self.get_logger().info(
                f"SPI initialized successfully on Bus {self.spi_bus}, Device {self.spi_device} at 1MHz."
            )
        except PermissionError:
            self.get_logger().error(
                "Permission denied accessing SPI! Run: 'sudo usermod -aG spi $USER' and reboot."
            )
        except Exception as e:
            self.get_logger().error(f"Failed to open SPI port: {e}")

    def brake_callback(self, msg: Float32):
        brake_val = msg.data
        
        try:
            # Convert the float into exactly 4 bytes (Little-Endian format for ESP)
            # '<f' means Little-Endian Float.
            byte_array = list(struct.pack('<f', brake_val))
            
            # Send the 4 bytes over the SPI bus
            self.spi.xfer2(byte_array)
            
            self.get_logger().info(
                f"SPI TX -> Brake: {brake_val:.1f} | Raw Bytes: [0x{byte_array[0]:02x}, 0x{byte_array[1]:02x}, 0x{byte_array[2]:02x}, 0x{byte_array[3]:02x}]"
            )
            
        except Exception as e:
            self.get_logger().error(f"SPI Transmit Error: {e}")

    def destroy_node(self):
        # Always close the SPI bus gracefully on shutdown
        self.spi.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SPIBridgeNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("SPI Bridge node shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()