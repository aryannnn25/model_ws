// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from radar_interfaces:msg/RadarMessage.idl
// generated code does not contain a copyright notice

#ifndef RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__STRUCT_HPP_
#define RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__radar_interfaces__msg__RadarMessage __attribute__((deprecated))
#else
# define DEPRECATED__radar_interfaces__msg__RadarMessage __declspec(deprecated)
#endif

namespace radar_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct RadarMessage_
{
  using Type = RadarMessage_<ContainerAllocator>;

  explicit RadarMessage_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->target_id = 0l;
      this->x = 0.0f;
      this->y = 0.0f;
      this->v = 0.0f;
      this->rcs = 0.0f;
      this->r = 0.0f;
      this->angle = 0.0f;
    }
  }

  explicit RadarMessage_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->target_id = 0l;
      this->x = 0.0f;
      this->y = 0.0f;
      this->v = 0.0f;
      this->rcs = 0.0f;
      this->r = 0.0f;
      this->angle = 0.0f;
    }
  }

  // field types and members
  using _target_id_type =
    int32_t;
  _target_id_type target_id;
  using _x_type =
    float;
  _x_type x;
  using _y_type =
    float;
  _y_type y;
  using _v_type =
    float;
  _v_type v;
  using _rcs_type =
    float;
  _rcs_type rcs;
  using _r_type =
    float;
  _r_type r;
  using _angle_type =
    float;
  _angle_type angle;

  // setters for named parameter idiom
  Type & set__target_id(
    const int32_t & _arg)
  {
    this->target_id = _arg;
    return *this;
  }
  Type & set__x(
    const float & _arg)
  {
    this->x = _arg;
    return *this;
  }
  Type & set__y(
    const float & _arg)
  {
    this->y = _arg;
    return *this;
  }
  Type & set__v(
    const float & _arg)
  {
    this->v = _arg;
    return *this;
  }
  Type & set__rcs(
    const float & _arg)
  {
    this->rcs = _arg;
    return *this;
  }
  Type & set__r(
    const float & _arg)
  {
    this->r = _arg;
    return *this;
  }
  Type & set__angle(
    const float & _arg)
  {
    this->angle = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    radar_interfaces::msg::RadarMessage_<ContainerAllocator> *;
  using ConstRawPtr =
    const radar_interfaces::msg::RadarMessage_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<radar_interfaces::msg::RadarMessage_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<radar_interfaces::msg::RadarMessage_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      radar_interfaces::msg::RadarMessage_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<radar_interfaces::msg::RadarMessage_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      radar_interfaces::msg::RadarMessage_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<radar_interfaces::msg::RadarMessage_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<radar_interfaces::msg::RadarMessage_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<radar_interfaces::msg::RadarMessage_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__radar_interfaces__msg__RadarMessage
    std::shared_ptr<radar_interfaces::msg::RadarMessage_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__radar_interfaces__msg__RadarMessage
    std::shared_ptr<radar_interfaces::msg::RadarMessage_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const RadarMessage_ & other) const
  {
    if (this->target_id != other.target_id) {
      return false;
    }
    if (this->x != other.x) {
      return false;
    }
    if (this->y != other.y) {
      return false;
    }
    if (this->v != other.v) {
      return false;
    }
    if (this->rcs != other.rcs) {
      return false;
    }
    if (this->r != other.r) {
      return false;
    }
    if (this->angle != other.angle) {
      return false;
    }
    return true;
  }
  bool operator!=(const RadarMessage_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct RadarMessage_

// alias to use template instance with default allocator
using RadarMessage =
  radar_interfaces::msg::RadarMessage_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace radar_interfaces

#endif  // RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__STRUCT_HPP_
