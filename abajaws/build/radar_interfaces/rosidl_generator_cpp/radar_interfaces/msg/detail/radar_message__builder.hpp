// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from radar_interfaces:msg/RadarMessage.idl
// generated code does not contain a copyright notice

#ifndef RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__BUILDER_HPP_
#define RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "radar_interfaces/msg/detail/radar_message__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace radar_interfaces
{

namespace msg
{

namespace builder
{

class Init_RadarMessage_angle
{
public:
  explicit Init_RadarMessage_angle(::radar_interfaces::msg::RadarMessage & msg)
  : msg_(msg)
  {}
  ::radar_interfaces::msg::RadarMessage angle(::radar_interfaces::msg::RadarMessage::_angle_type arg)
  {
    msg_.angle = std::move(arg);
    return std::move(msg_);
  }

private:
  ::radar_interfaces::msg::RadarMessage msg_;
};

class Init_RadarMessage_r
{
public:
  explicit Init_RadarMessage_r(::radar_interfaces::msg::RadarMessage & msg)
  : msg_(msg)
  {}
  Init_RadarMessage_angle r(::radar_interfaces::msg::RadarMessage::_r_type arg)
  {
    msg_.r = std::move(arg);
    return Init_RadarMessage_angle(msg_);
  }

private:
  ::radar_interfaces::msg::RadarMessage msg_;
};

class Init_RadarMessage_rcs
{
public:
  explicit Init_RadarMessage_rcs(::radar_interfaces::msg::RadarMessage & msg)
  : msg_(msg)
  {}
  Init_RadarMessage_r rcs(::radar_interfaces::msg::RadarMessage::_rcs_type arg)
  {
    msg_.rcs = std::move(arg);
    return Init_RadarMessage_r(msg_);
  }

private:
  ::radar_interfaces::msg::RadarMessage msg_;
};

class Init_RadarMessage_v
{
public:
  explicit Init_RadarMessage_v(::radar_interfaces::msg::RadarMessage & msg)
  : msg_(msg)
  {}
  Init_RadarMessage_rcs v(::radar_interfaces::msg::RadarMessage::_v_type arg)
  {
    msg_.v = std::move(arg);
    return Init_RadarMessage_rcs(msg_);
  }

private:
  ::radar_interfaces::msg::RadarMessage msg_;
};

class Init_RadarMessage_y
{
public:
  explicit Init_RadarMessage_y(::radar_interfaces::msg::RadarMessage & msg)
  : msg_(msg)
  {}
  Init_RadarMessage_v y(::radar_interfaces::msg::RadarMessage::_y_type arg)
  {
    msg_.y = std::move(arg);
    return Init_RadarMessage_v(msg_);
  }

private:
  ::radar_interfaces::msg::RadarMessage msg_;
};

class Init_RadarMessage_x
{
public:
  explicit Init_RadarMessage_x(::radar_interfaces::msg::RadarMessage & msg)
  : msg_(msg)
  {}
  Init_RadarMessage_y x(::radar_interfaces::msg::RadarMessage::_x_type arg)
  {
    msg_.x = std::move(arg);
    return Init_RadarMessage_y(msg_);
  }

private:
  ::radar_interfaces::msg::RadarMessage msg_;
};

class Init_RadarMessage_target_id
{
public:
  Init_RadarMessage_target_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_RadarMessage_x target_id(::radar_interfaces::msg::RadarMessage::_target_id_type arg)
  {
    msg_.target_id = std::move(arg);
    return Init_RadarMessage_x(msg_);
  }

private:
  ::radar_interfaces::msg::RadarMessage msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::radar_interfaces::msg::RadarMessage>()
{
  return radar_interfaces::msg::builder::Init_RadarMessage_target_id();
}

}  // namespace radar_interfaces

#endif  // RADAR_INTERFACES__MSG__DETAIL__RADAR_MESSAGE__BUILDER_HPP_
