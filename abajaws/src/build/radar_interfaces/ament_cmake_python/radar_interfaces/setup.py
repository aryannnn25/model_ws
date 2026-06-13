from setuptools import find_packages
from setuptools import setup

setup(
    name='radar_interfaces',
    version='0.0.0',
    packages=find_packages(
        include=('radar_interfaces', 'radar_interfaces.*')),
)
