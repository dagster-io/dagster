# If necessary, uncomment the line below to include explore_source.
include: "/explores/*.lkml"

view: customer_event_fact {
  derived_table: {
    datagroup_trigger: new_day
    explore_source: omni_channel_events_base {
      column: customer_id {}
      column: acquisition_source {}
      column: cart_adds {}
      column: event_count {}
      column: purchases {}
      column: session_count {}
    }
  }
  dimension: customer_id {
    type: number
  }
  dimension: acquisition_source {
    type: string
  }
  dimension: cart_adds {
    type: number
  }
  dimension: event_count {
    type: number
  }
  dimension: purchases {
    type: number
  }
  dimension: session_count {
    type: number
  }
}
