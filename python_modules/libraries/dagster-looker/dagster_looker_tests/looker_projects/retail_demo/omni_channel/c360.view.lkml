# If necessary, uncomment the line below to include explore_source.
include: "/models/omni_channel.model.lkml"

view: c360 {
  derived_table: {
    datagroup_trigger: new_day
    explore_source: customer_transaction_fact {
      column: cart_adds { field: customer_event_fact.cart_adds }
      column: event_count { field: customer_event_fact.event_count }
      column: purchases { field: customer_event_fact.purchases }
      column: session_count { field: customer_event_fact.session_count }
      column: count { field: customer_support_fact.count }
      column: acquisition_source {field: customer_event_fact.acquisition_source}
      column: curbside_transaction_count {}
      column: customer_id {}
      column: discounted_transaction_count {}
      column: first_purchase {}
      column: instore_transaction_count {}
      column: item_count {}
      column: l180_transaction_count {}
      column: l30_transaction_count {}
      column: l360_transaction_count {}
      column: l90_transaction_count {}
      column: last_purchase {}
      column: online_transaction_count {}
      column: return_count {}
      column: total_sales {}
      column: transaction_count {}
    }
  }
  dimension: acquisition_source {
    drill_fields: [omni_channel_transactions.offer_type]
    type: string
    sql: COALESCE(${TABLE}.acquisition_source,'Unknown') ;;
  }
  dimension: customer_type {
    drill_fields: [acquisition_source,has_visited_website]
    case: {
      when: {
        sql: ${online_transaction_count} > 0 and ${instore_transaction_count} > 0 ;;
        label: "Online Only"
      }
      when: {
        sql: ${online_transaction_count} > 0 and ${instore_transaction_count} = 0 ;;
        label: "Instore Only"
      }
      when: {
        sql: ${online_transaction_count} = 0 and ${instore_transaction_count} > 0 ;;
        label: "Both Online and Instore"
      }

    }
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
  dimension: has_visited_website {
    type: yesno
    sql: ${event_count} > 0 ;;
  }
  dimension: count {
    label: "Support Calls"
    type: number
  }
  dimension: curbside_transaction_count {
    type: number
  }
  dimension: customer_id {
    value_format_name: id
    primary_key: yes
    type: number
  }
  dimension: discounted_transaction_count {
    type: number
  }
  dimension_group: first_purchase {
    type: time
    timeframes: [raw,date]
    sql: CAST(${TABLE}.first_purchase as timestamp) ;;
  }
  dimension: instore_transaction_count {
    type: number
  }
  dimension: item_count {
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
  dimension_group: last_purchase {
    type: time
    timeframes: [raw,date]
    sql: CAST(${TABLE}.last_purchase as timestamp) ;;
  }
  dimension: days_a_customer {
    type: number
    sql: IF(DATE_DIFF(CURRENT_DATE(), ${first_purchase_date}, DAY) > 30,DATE_DIFF(CURRENT_DATE(), ${first_purchase_date}, DAY),30) ;;
  }
  dimension: days_since_last_purchase {
    type: number
    sql: DATE_DIFF(CURRENT_DATE(), ${last_purchase_date}, DAY) ;;
  }
  dimension: average_days_between_transaction {
    type: number
    sql: ${days_a_customer} / nullif(${purchases},0) ;;
  }
  dimension: risk_of_churn {
    type: number
    value_format_name: percent_1
    sql: IF(1 - (${average_days_between_transaction} / nullif(${days_since_last_purchase},0))<0,0,1 - (${average_days_between_transaction} / nullif(${days_since_last_purchase},0))) ;;
  }
  dimension: risk_of_churn_100 {
    type: number
    sql: ${risk_of_churn} * 100 ;;
  }
  dimension: online_transaction_count {
    type: number
  }
  dimension: return_count {
    type: number
  }
  dimension: total_sales {
    value_format_name: usd
    type: number
  }
  dimension: transaction_count {
    type: number
  }

#use customer transaction date

  dimension: months_since_first_purchase {
    type: number
    sql: DATE_DIFF(${omni_channel_transactions.transaction_date}, ${first_purchase_date}, MONTH) ;;
  }

  dimension: transactions_per_month {
    type: number
    sql: ${transaction_count}/nullif(${months_since_first_purchase},0) ;;
  }

  dimension: recency_rating {
    hidden: yes
    type: number
    sql: CASE WHEN ${l30_transaction_count} >= 1 THEN 5
              WHEN ${l30_transaction_count} < 1 AND ${l90_transaction_count} >=1 THEN 4
              WHEN ${l30_transaction_count} < 1 AND ${l90_transaction_count} < 1 AND ${l180_transaction_count} >= 1 THEN 3
              WHEN ${l30_transaction_count} < 1 AND ${l90_transaction_count} < 1 AND ${l180_transaction_count} < 1 AND ${l360_transaction_count} >= 2 THEN 2
              WHEN ${l360_transaction_count} < 2 THEN 1
              ELSE null
              END ;;
  }

# number of transactions/orders per month
  dimension: frequency_rating {
    hidden: yes
    type: number
    sql: CASE WHEN ${transactions_per_month} >= 2 THEN 5
              WHEN ${transactions_per_month} >= 1 THEN 4
              WHEN ${transactions_per_month} >= 0.5 THEN 3
              WHEN ${transactions_per_month} >= 0.25 THEN 2
              else 1
              END ;;
  }

  dimension: value_rating {
    hidden: yes
    type: number
    sql: CASE WHEN ${total_sales} >= 1000 THEN 5
              WHEN ${total_sales} < 1000 AND ${total_sales} >= 800 THEN 4
              WHEN ${total_sales} < 800 AND ${total_sales} >= 600 THEN 3
              WHEN ${total_sales} < 600 AND ${total_sales} >= 400 THEN 2
              WHEN ${total_sales} < 400 THEN 1
              ELSE null
              END ;;
  }

  dimension: rfm_rating {
    type: string
    sql: CASE WHEN ${recency_rating} = 5 AND (${frequency_rating} = 5 OR ${frequency_rating} = 4) THEN 'Champion'
              WHEN (${recency_rating} = 5 OR ${recency_rating} = 4) AND (${frequency_rating} = 3 OR ${frequency_rating} = 2) THEN 'Potential Loyalist'
              WHEN ${recency_rating} = 5 AND ${frequency_rating} = 1 THEN 'New Customer'
              WHEN ${recency_rating} = 4 AND ${frequency_rating} = 1 THEN 'Promising'
              WHEN (${recency_rating} = 4 OR ${recency_rating} = 3) AND (${frequency_rating} = 5 OR ${frequency_rating} = 4) THEN 'Loyal Customer'
              WHEN (${recency_rating} = 2 OR ${recency_rating} = 1) AND ${frequency_rating} = 5 THEN 'Cant lose them'
              WHEN (${recency_rating} = 2 OR ${recency_rating} = 1) AND (${frequency_rating} = 4 OR ${frequency_rating} = 3) THEN 'At Risk'
              WHEN ${recency_rating} = 3 AND ${frequency_rating} = 3 THEN 'Needs Attention'
              WHEN (${recency_rating} = 2 OR ${recency_rating} = 1) AND (${frequency_rating} = 2 OR ${frequency_rating} = 1) THEN 'Hibernating'
              WHEN ${recency_rating} = 3 AND (${frequency_rating} = 2 OR ${frequency_rating} = 1) THEN 'About to sleep'
              ELSE null
              END ;;
  }

  measure: customer_count {
    value_format:"[>=1000000]0.0,,\"M\";[>=1000]0.0,\"K\";0"
    drill_fields: [customer_id,customers.name,customers.email,customers.address,retail_clv_predict.predicted_clv,risk_of_churn,omni_channel_transactions__transaction_details.recommended_products]
    link: {
      label: "Top 100 Predicted CLV Customers"
      url: "{{ link }}&sorts=c360.predicted_clv+desc&limit=100"
    }
    type: count
  }

  measure: high_recency_customers {
    group_label: "RFV Analysis"
    type: count
    filters: [recency_rating: "5"]
  }

  measure: low_recency_customers {
    group_label: "RFV Analysis"
    type: count
    filters: [recency_rating: "1"]
  }

  measure: high_frequency_customers {
    group_label: "RFV Analysis"
    type: count
    filters: [frequency_rating: "5"]
  }

  measure: low_frequency_customers {
    group_label: "RFV Analysis"
    type: count
    filters: [frequency_rating: "1"]
  }

  measure: average_sales_amount {
    value_format:"[>=1000000]$0.0,,\"M\";[>=1000]$0.0,\"K\";$0.0"
    type: average
    sql: ${total_sales} ;;
  }

  measure: average_transaction_count {
    type: average
    sql: ${transaction_count} ;;
  }

  measure: high_monetary_value_customers {
    group_label: "RFV Analysis"
    type: count
    filters: [value_rating: "5"]
  }

  measure: low_monetary_value_customers {
    group_label: "RFV Analysis"
    type: count
    filters: [value_rating: "1"]
  }

  # using retail_clv_predict.predicted_clv for CLV metrics below
  # see colab: https://colab.research.google.com/drive/1eLUqHgAv8gJig61t8NgrVzT7uv_pqsFi?resourcekey=0-E5aEzPTb44U80SLiE4NMvg&usp=sharing
  # view with predictions: https://googledemo.looker.com/projects/retail/files/omni_channel/lpd_retail_clv_predict_tbl.view.lkml

  # dimension: predicted_clv {
  #   value_format:"[>=1000000]$0.0,,\"M\";[>=1000]$0.0,\"K\";$0.0"
  #   type: number
  #   sql: (${total_sales} / NULLIF(${days_a_customer},0) * 365) / IF(${customer_type} = 'Both Online and Instore',0.05,0.1) ;;
  # }

  # measure: average_clv {
  #   value_format:"[>=1000000]$0.0,,\"M\";[>=1000]$0.0,\"K\";$0.0"
  #   type: average
  #   sql: ${predicted_clv} ;;
  # }

  # measure: customer_count_first_purchase {
  #   type: count
  #   filters: [months_since_first_purchase: "0"]
  # }

  # measure: sales_per_user {
  #   type: number
  #   sql: ${omni_channel_transactions__transaction_details.total_sales}/${customer_count_first_purchase} ;;
  # }
}
