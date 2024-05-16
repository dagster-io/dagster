# If necessary, uncomment the line below to include explore_source.
include: "/models/omni_channel.model.lkml"

view: customer_support_fact {
  derived_table: {
    datagroup_trigger: new_day
    explore_source: omni_channel_support_calls {
      column: client_id {}
      column: count {}
    }
  }
  dimension: client_id {
    type: number
  }
  dimension: count {
    type: number
  }
}
