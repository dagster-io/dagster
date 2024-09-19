include: "date_comparison.view.lkml"

view: transactions {
  sql_table_name: `looker-private-demo.retail.transaction_detail` ;;
  extends: [date_comparison]


  dimension: transaction_id {
    type: number
    primary_key: yes
    sql: ${TABLE}.transaction_id ;;
  }

  dimension: channel_id {
    type: number
    hidden: yes
    sql: ${TABLE}.channel_id ;;
  }

  dimension: customer_id {
    type: number
    hidden: yes
    sql: ${TABLE}.customer_id ;;
  }

  dimension: line_items {
    hidden: yes
    sql:
    -- spectacles: ignore
    ${TABLE}.line_items ;;
  }

  dimension: store_id {
    type: number
    hidden: yes
    sql: ${TABLE}.store_id ;;
  }

  dimension_group: transaction {
    type: time
    timeframes: [
      raw,
      time,
      date,
      day_of_week,
      hour_of_day,
      week,
      month,
      quarter,
      year,
      week_of_year,
      month_num
    ]
    sql: ${TABLE}.transaction_timestamp ;;
  }

  ##### DERIVED DIMENSIONS #####

  extends: [date_comparison]

  set: drill_detail {
    fields: [transaction_date, stores.name, products.area, products.name, transactions__line_items.total_sales, number_of_transactions]
  }

  dimension_group: since_first_customer_transaction {
    type: duration
    intervals: [month]
    sql_start: ${customer_facts.customer_first_purchase_raw} ;;
    sql_end: ${transaction_raw} ;;
  }

  ##### MEASURES #####

  measure: number_of_transactions {
    type: count_distinct
    sql: ${transactions.transaction_id} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: number_of_customers {
    type: count_distinct
    sql: ${transactions.customer_id} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: number_of_stores {
    view_label: "Stores 🏪"
    type: count_distinct
    sql: ${transactions.store_id} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: number_of_customer_transactions {
    hidden: yes
    type: count_distinct
    sql: ${transaction_id} ;;
    filters: {
      field: customer_id
      value: "NOT NULL"
    }
  }

  measure: percent_customer_transactions {
    type: number
    sql: ${number_of_customer_transactions}/NULLIF(${number_of_transactions},0) ;;
    value_format_name: percent_1
    drill_fields: [drill_detail*]
  }

  measure: first_transaction {
    type: date
    sql: MIN(${transaction_raw}) ;;
    drill_fields: [drill_detail*]
  }

  ##### DATE COMPARISON MEASURES #####

  measure: number_of_transactions_change {
    view_label: "Date Comparison"
    label: "Number of Transactions Change (%)"
    type: number
    sql: COUNT(distinct CASE WHEN ${transactions.selected_comparison} LIKE 'This%' THEN ${transaction_id} ELSE NULL END) / NULLIF(COUNT(distinct CASE WHEN ${transactions.selected_comparison} LIKE 'Prior%' THEN ${transaction_id} ELSE NULL END),0) -1;;
    value_format_name: percent_1
    drill_fields: [drill_detail*]
  }

  measure: number_of_customers_change {
    view_label: "Date Comparison"
    label: "Number of Customers Change (%)"
    type: number
    sql: COUNT(distinct CASE WHEN ${transactions.selected_comparison} LIKE 'This%' THEN ${customer_id} ELSE NULL END) / NULLIF(COUNT(distinct CASE WHEN ${transactions.selected_comparison} LIKE 'Prior%' THEN ${customer_id} ELSE NULL END),0) -1;;
    value_format_name: percent_1
    drill_fields: [drill_detail*]
  }

  ##### PER STORE MEASURES #####

  measure: number_of_transactions_per_store {
    view_label: "Stores 🏪"
    type: number
    sql: ${number_of_transactions}/NULLIF(${number_of_stores},0) ;;
    value_format_name: decimal_0
    drill_fields: [transactions.drill_detail*]
  }
}
