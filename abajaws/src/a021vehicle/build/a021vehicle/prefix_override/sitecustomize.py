import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/a-baja/abajaws/src/a021vehicle/install/a021vehicle'
