#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "radar_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__radar_interfaces__msg__RadarMessage() -> *const std::ffi::c_void;
}

#[link(name = "radar_interfaces__rosidl_generator_c")]
extern "C" {
    fn radar_interfaces__msg__RadarMessage__init(msg: *mut RadarMessage) -> bool;
    fn radar_interfaces__msg__RadarMessage__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<RadarMessage>, size: usize) -> bool;
    fn radar_interfaces__msg__RadarMessage__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<RadarMessage>);
    fn radar_interfaces__msg__RadarMessage__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<RadarMessage>, out_seq: *mut rosidl_runtime_rs::Sequence<RadarMessage>) -> bool;
}

// Corresponds to radar_interfaces__msg__RadarMessage
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct RadarMessage {

    // This member is not documented.
    #[allow(missing_docs)]
    pub target_id: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub v: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub rcs: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub r: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub angle: f32,

}



impl Default for RadarMessage {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !radar_interfaces__msg__RadarMessage__init(&mut msg as *mut _) {
        panic!("Call to radar_interfaces__msg__RadarMessage__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for RadarMessage {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { radar_interfaces__msg__RadarMessage__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { radar_interfaces__msg__RadarMessage__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { radar_interfaces__msg__RadarMessage__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for RadarMessage {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for RadarMessage where Self: Sized {
  const TYPE_NAME: &'static str = "radar_interfaces/msg/RadarMessage";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__radar_interfaces__msg__RadarMessage() }
  }
}


