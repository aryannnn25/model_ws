#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to radar_interfaces__msg__RadarMessage

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::RadarMessage::default())
  }
}

impl rosidl_runtime_rs::Message for RadarMessage {
  type RmwMsg = super::msg::rmw::RadarMessage;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        target_id: msg.target_id,
        x: msg.x,
        y: msg.y,
        v: msg.v,
        rcs: msg.rcs,
        r: msg.r,
        angle: msg.angle,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      target_id: msg.target_id,
      x: msg.x,
      y: msg.y,
      v: msg.v,
      rcs: msg.rcs,
      r: msg.r,
      angle: msg.angle,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      target_id: msg.target_id,
      x: msg.x,
      y: msg.y,
      v: msg.v,
      rcs: msg.rcs,
      r: msg.r,
      angle: msg.angle,
    }
  }
}


