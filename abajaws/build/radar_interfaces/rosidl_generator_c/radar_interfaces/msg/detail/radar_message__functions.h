// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from radar_interfaces:msg/RadarMessage.idl
// generated code does not contain a copyright notice

#ifndef RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__FUNCTIONS_H_
#define RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "radar_interfaces/msg/rosidl_generator_c__visibility_control.h"

#include "radar_interfaces/msg/detail/radar_message__struct.h"

/// Initialize msg/RadarMessage message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * radar_interfaces__msg__RadarMessage
 * )) before or use
 * radar_interfaces__msg__RadarMessage__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
bool
radar_interfaces__msg__RadarMessage__init(radar_interfaces__msg__RadarMessage * msg);

/// Finalize msg/RadarMessage message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
void
radar_interfaces__msg__RadarMessage__fini(radar_interfaces__msg__RadarMessage * msg);

/// Create msg/RadarMessage message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * radar_interfaces__msg__RadarMessage__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
radar_interfaces__msg__RadarMessage *
radar_interfaces__msg__RadarMessage__create();

/// Destroy msg/RadarMessage message.
/**
 * It calls
 * radar_interfaces__msg__RadarMessage__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
void
radar_interfaces__msg__RadarMessage__destroy(radar_interfaces__msg__RadarMessage * msg);

/// Check for msg/RadarMessage message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
bool
radar_interfaces__msg__RadarMessage__are_equal(const radar_interfaces__msg__RadarMessage * lhs, const radar_interfaces__msg__RadarMessage * rhs);

/// Copy a msg/RadarMessage message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
bool
radar_interfaces__msg__RadarMessage__copy(
  const radar_interfaces__msg__RadarMessage * input,
  radar_interfaces__msg__RadarMessage * output);

/// Initialize array of msg/RadarMessage messages.
/**
 * It allocates the memory for the number of elements and calls
 * radar_interfaces__msg__RadarMessage__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
bool
radar_interfaces__msg__RadarMessage__Sequence__init(radar_interfaces__msg__RadarMessage__Sequence * array, size_t size);

/// Finalize array of msg/RadarMessage messages.
/**
 * It calls
 * radar_interfaces__msg__RadarMessage__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
void
radar_interfaces__msg__RadarMessage__Sequence__fini(radar_interfaces__msg__RadarMessage__Sequence * array);

/// Create array of msg/RadarMessage messages.
/**
 * It allocates the memory for the array and calls
 * radar_interfaces__msg__RadarMessage__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
radar_interfaces__msg__RadarMessage__Sequence *
radar_interfaces__msg__RadarMessage__Sequence__create(size_t size);

/// Destroy array of msg/RadarMessage messages.
/**
 * It calls
 * radar_interfaces__msg__RadarMessage__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
void
radar_interfaces__msg__RadarMessage__Sequence__destroy(radar_interfaces__msg__RadarMessage__Sequence * array);

/// Check for msg/RadarMessage message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
bool
radar_interfaces__msg__RadarMessage__Sequence__are_equal(const radar_interfaces__msg__RadarMessage__Sequence * lhs, const radar_interfaces__msg__RadarMessage__Sequence * rhs);

/// Copy an array of msg/RadarMessage messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_radar_interfaces
bool
radar_interfaces__msg__RadarMessage__Sequence__copy(
  const radar_interfaces__msg__RadarMessage__Sequence * input,
  radar_interfaces__msg__RadarMessage__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__FUNCTIONS_H_
