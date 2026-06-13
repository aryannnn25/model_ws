"""from setuptools import find_packages, setup

package_name = 'a021vehicle'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    package_data={
        package_name: [
            '*.so',
            '*.h',
        ],
    },
    install_requires=['setuptools'],
    zip_safe=False,
    maintainer='a-baja',
    maintainer_email='a-baja@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'radar_node = a021vehicle.rawradar:main',
            'vehiclecontrol = a021vehicle.vehiclecontrol:main',
            'receiver_node = a021vehicle.radar_receiver:main',
            'radar_data = a021vehicle.radar_data:main',
            # 'spi_bridge = a021vehicle.radar_spi_bridge:main',
            'esp_bridge = a021vehicle.ros_esp_bridge:main',
        ],
    },
)
"""
import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'a021vehicle'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # --- ADD THIS LINE TO INCLUDE LAUNCH FILES ---
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.py'))),
    ],
    install_requires=['setuptools'],
    zip_safe=False,
    maintainer='a-baja',
    maintainer_email='a-baja@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'radar_node = a021vehicle.rawradar:main',
            'vehiclecontrol = a021vehicle.vehiclecontrol:main',
            'receiver_node = a021vehicle.radar_receiver:main',
            'radar_data = a021vehicle.radar_data:main',
            # 'spi_bridge = a021vehicle.radar_spi_bridge:main',
            'esp_bridge = a021vehicle.ros_esp_bridge:main',
        ],
    },
)
