// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from radar_interfaces:msg/RadarMessage.idl
// generated code does not contain a copyright notice

#ifndef RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__STRUCT_H_
#define RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in msg/RadarMessage in the package radar_interfaces.
typedef struct radar_interfaces__msg__RadarMessage
{
  int32_t target_id;
  float x;
  float y;
  float v;
  float rcs;
  float r;
  float angle;
} radar_interfaces__msg__RadarMessage;

// Struct for a sequence of radar_interfaces__msg__RadarMessage.
typedef struct radar_interfaces__msg__RadarMessage__Sequence
{
  radar_interfaces__msg__RadarMessage * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} radar_interfaces__msg__RadarMessage__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__STRUCT_H_
