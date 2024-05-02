connection: "looker-private-demo"

include: "/omni_channel/*.view.lkml"
include: "/omni_channel/*.dashboard.lookml"


datagroup: new_day {
  sql_trigger: SELECT CURRENT_DATE() ;;
  max_cache_age: "24 hours"
}

explore: omni_channel_transactions {
  description: "#audience-builder" # for audience builder extension
  persist_with: new_day
  join: omni_channel_transactions__transaction_details {
    type: left_outer
    relationship: one_to_many
    sql: LEFT JOIN UNNEST(${omni_channel_transactions.transaction_details}) as omni_channel_transactions__transaction_details  ;;
  }
  join: c360 {
    type: inner
    relationship: many_to_one
    sql_on: ${omni_channel_transactions.customer_id} = ${c360.customer_id} ;;
  }
  join: customers {
    type: inner
    relationship: one_to_one
    sql_on: ${c360.customer_id} = ${customers.id} ;;
  }
  join: retail_clv_predict {
    view_label: "C360"
    fields: [predicted_clv, average_clv]
    relationship: one_to_one
    sql_on: ${c360.customer_id} = ${retail_clv_predict.customer_id} ;;
  }
}

explore: omni_channel_events {
  persist_with: new_day
  join: c360 {
    type: inner
    relationship: many_to_one
    sql_on: ${c360.customer_id} = ${omni_channel_events.customer_id} ;;
  }
  join: omni_channel_transactions {
    fields: []
    relationship: one_to_many
    sql_on: ${omni_channel_transactions.customer_id} = ${c360.customer_id} ;;
  }
  join: omni_channel_transactions__transaction_details {
    fields: [omni_channel_transactions__transaction_details.total_sales]
    type: left_outer
    relationship: one_to_many
    sql: LEFT JOIN UNNEST(${omni_channel_transactions.transaction_details}) as omni_channel_transactions__transaction_details  ;;
  }
  join: retail_clv_predict {
    view_label: "C360"
    fields: [predicted_clv, average_clv]
    relationship: one_to_one
    sql_on: ${c360.customer_id} = ${retail_clv_predict.customer_id} ;;
  }
}

explore: omni_channel_support_calls {
  persist_with: new_day
}

explore: customer_event_fact {}


explore: customer_transaction_fact {
  persist_with: new_day
  join: customer_event_fact {
    type: left_outer
    relationship: one_to_one
    sql_on: ${customer_event_fact.customer_id} = ${customer_transaction_fact.customer_id} ;;
  }
  join: customer_support_fact {
    type: left_outer
    relationship: one_to_one
    sql_on: ${customer_support_fact.client_id} = ${customer_transaction_fact.customer_id} ;;
  }
}
