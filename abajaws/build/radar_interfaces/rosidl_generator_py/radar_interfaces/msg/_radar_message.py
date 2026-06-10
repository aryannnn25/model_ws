# generated from rosidl_generator_py/resource/_idl.py.em
# with input from radar_interfaces:msg/RadarMessage.idl
# generated code does not contain a copyright notice


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_RadarMessage(type):
    """Metaclass of message 'RadarMessage'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('radar_interfaces')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'radar_interfaces.msg.RadarMessage')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__radar_message
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__radar_message
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__radar_message
            cls._TYPE_SUPPORT = module.type_support_msg__msg__radar_message
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__radar_message

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class RadarMessage(metaclass=Metaclass_RadarMessage):
    """Message class 'RadarMessage'."""

    __slots__ = [
        '_target_id',
        '_x',
        '_y',
        '_v',
        '_rcs',
        '_r',
        '_angle',
    ]

    _fields_and_field_types = {
        'target_id': 'int32',
        'x': 'float',
        'y': 'float',
        'v': 'float',
        'rcs': 'float',
        'r': 'float',
        'angle': 'float',
    }

    SLOT_TYPES = (
        rosidl_parser.definition.BasicType('int32'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
            'Invalid arguments passed to constructor: %s' % \
            ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        self.target_id = kwargs.get('target_id', int())
        self.x = kwargs.get('x', float())
        self.y = kwargs.get('y', float())
        self.v = kwargs.get('v', float())
        self.rcs = kwargs.get('rcs', float())
        self.r = kwargs.get('r', float())
        self.angle = kwargs.get('angle', float())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.__slots__, self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s[1:] + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.target_id != other.target_id:
            return False
        if self.x != other.x:
            return False
        if self.y != other.y:
            return False
        if self.v != other.v:
            return False
        if self.rcs != other.rcs:
            return False
        if self.r != other.r:
            return False
        if self.angle != other.angle:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def target_id(self):
        """Message field 'target_id'."""
        return self._target_id

    @target_id.setter
    def target_id(self, value):
        if __debug__:
            assert \
                isinstance(value, int), \
                "The 'target_id' field must be of type 'int'"
            assert value >= -2147483648 and value < 2147483648, \
                "The 'target_id' field must be an integer in [-2147483648, 2147483647]"
        self._target_id = value

    @builtins.property
    def x(self):
        """Message field 'x'."""
        return self._x

    @x.setter
    def x(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'x' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'x' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._x = value

    @builtins.property
    def y(self):
        """Message field 'y'."""
        return self._y

    @y.setter
    def y(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'y' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'y' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._y = value

    @builtins.property
    def v(self):
        """Message field 'v'."""
        return self._v

    @v.setter
    def v(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'v' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'v' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._v = value

    @builtins.property
    def rcs(self):
        """Message field 'rcs'."""
        return self._rcs

    @rcs.setter
    def rcs(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'rcs' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'rcs' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._rcs = value

    @builtins.property
    def r(self):
        """Message field 'r'."""
        return self._r

    @r.setter
    def r(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'r' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'r' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._r = value

    @builtins.property
    def angle(self):
        """Message field 'angle'."""
        return self._angle

    @angle.setter
    def angle(self, value):
        if __debug__:
            assert \
                isinstance(value, float), \
                "The 'angle' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'angle' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._angle = value
