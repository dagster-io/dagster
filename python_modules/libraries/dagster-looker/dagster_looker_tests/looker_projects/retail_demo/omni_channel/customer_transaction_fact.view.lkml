# If necessary, uncomment the line below to include explore_source.
include: "/models/omni_channel.model.lkml"

view: customer_transaction_fact {
  derived_table: {
    datagroup_trigger: new_day
    explore_source: omni_channel_transactions {
      column: customer_id {}
      column: curbside_transaction_count {}
      column: first_purchase {}
      column: instore_transaction_count {}
      column: l180_transaction_count {}
      column: l30_transaction_count {}
      column: l360_transaction_count {}
      column: l90_transaction_count {}
      column: last_purchase {}
      column: online_transaction_count {}
      column: total_sales { field: omni_channel_transactions__transaction_details.total_sales }
      column: item_count { field: omni_channel_transactions__transaction_details.item_count }
      column: transaction_count {}
      column: discounted_transaction_count {}
      column: return_count {}
    }
  }
  dimension: customer_id {
    value_format_name: id
    type: number
  }
  dimension: curbside_transaction_count {
    type: number
  }
  dimension: first_purchase {
    type: string
  }
  dimension: instore_transaction_count {
    type: number
  }
  dimension: l180_transaction_count {
    type: number
  }
  dimension: l30_transaction_count {
    type: number
  }
  dimension: l360_transaction_count {
    type: number
  }
  dimension: l90_transaction_count {
    type: number
  }
  dimension: last_purchase {
    type: string
  }
  dimension: online_transaction_count {
    type: number
  }
  dimension: total_sales {
    type: number
  }
  dimension: item_count {
    type: number
  }
  dimension: transaction_count {
    type: number
  }
  dimension: discounted_transaction_count {
    type: number
  }
  dimension: return_count {
    type: number
  }
}
