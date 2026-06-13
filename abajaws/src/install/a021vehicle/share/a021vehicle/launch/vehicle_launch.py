from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler  # Added RegisterEventHandler
from launch.event_handlers import OnProcessExit                  # Added OnProcessExit
from launch_ros.actions import Node

def generate_launch_description():
    
    # 1. Define the CAN configuration command
    setup_can = ExecuteProcess(
        cmd=[['sudo ip link set can1 down 2>/dev/null; ',
              'sudo ip link set can1 type can bitrate 1000000; ',
              'sudo ip link set can1 up']],
        shell=True
    )

    # 2. Define your ROS 2 nodes as variables (without putting them in the final list yet)
    radar_node = Node(
        package='a021vehicle',
        executable='radar_node',
        name='radar_node',
        output='screen'
    )
    
    radar_data_node = Node(
        package='a021vehicle',
        executable='radar_data',
        name='radar_data_node',
        output='screen'
    )
    
    vehicle_control_node = Node(
        package='a021vehicle',
        executable='vehiclecontrol',
        name='vehicle_control_node',
        output='screen'
    )
    
    esp_bridge_node = Node(
        package='a021vehicle',
        executable='esp_bridge',
        name='esp_bridge_node',
        output='screen'
    )

    # 3. Create an Event Handler that waits for 'setup_can' to completely FINISH (exit)
    #    Before it allows the nodes to launch.
    launch_nodes_after_can = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=setup_can,
            on_exit=[
                radar_node,
                radar_data_node,
                vehicle_control_node,
                esp_bridge_node
            ]
        )
    )

    # 4. Return the LaunchDescription, starting ONLY with the CAN setup command
    return LaunchDescription([
        setup_can,
        launch_nodes_after_can
    ])