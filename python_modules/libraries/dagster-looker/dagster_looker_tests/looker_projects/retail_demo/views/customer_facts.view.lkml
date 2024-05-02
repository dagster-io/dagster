view: customer_facts {
  view_label: "Customers"
  derived_table: {
    sql: SELECT
        customer_id,
        SUM(sale_price)/NULLIF(COUNT(DISTINCT transaction_id ),0)  AS customer_average_basket_size,
        SUM(gross_margin) AS customer_lifetime_gross_margin,
        SUM(sale_price) AS customer_lifetime_sales,
        COUNT(DISTINCT transaction_id) AS customer_lifetime_transactions,
        SUM(1) AS customer_lifetime_quantity,
        MIN(transaction_timestamp) AS customer_first_purchase_date,
        SUM(CASE WHEN transaction_timestamp >= TIMESTAMP(DATE_ADD(CURRENT_DATE(),INTERVAL -6 MONTH)) AND transaction_timestamp < CURRENT_TIMESTAMP() THEN sale_price ELSE NULL END)
          /NULLIF(SUM(CASE WHEN transaction_timestamp >= TIMESTAMP(DATE_ADD(CURRENT_DATE(),INTERVAL -12 MONTH)) AND transaction_timestamp < TIMESTAMP(DATE_ADD(CURRENT_DATE(),INTERVAL -6 MONTH)) THEN sale_price ELSE NULL END),0) -1
          AS customer_spend_trend_past_year
      FROM ${transactions.SQL_TABLE_NAME} orders
      LEFT JOIN UNNEST(line_items) line_items
      GROUP BY 1 ;;
      datagroup_trigger: daily
      partition_keys: ["customer_first_purchase_date"]
      cluster_keys: ["customer_id"]
  }

  dimension: customer_id {
    type: number
    hidden: yes
    sql: ${TABLE}.customer_id ;;
  }

  dimension: customer_average_basket_size {
    type: number
    group_label: "Customer Lifetime"
    sql: ${TABLE}.customer_average_basket_size ;;
  }

  dimension: customer_lifetime_gross_margin {
    type: number
    group_label: "Customer Lifetime"
    sql: ${TABLE}.customer_lifetime_gross_margin ;;
  }

  dimension: customer_lifetime_sales {
    type: number
    group_label: "Customer Lifetime"
    sql: ${TABLE}.customer_lifetime_sales ;;
  }

  dimension: customer_lifetime_transactions {
    type: number
    group_label: "Customer Lifetime"
    sql: ${TABLE}.customer_lifetime_transactions ;;
  }

  dimension: customer_lifetime_quantity {
    type: number
    group_label: "Customer Lifetime"
    sql: ${TABLE}.customer_lifetime_quantity ;;
  }

  dimension_group: customer_first_purchase {
    type: time
    group_label: "Customer Lifetime"
    timeframes: [raw,date,week,month]
    sql: ${TABLE}.customer_first_purchase_date ;;
  }

  dimension: customer_spend_trend_past_year {
    type: number
    group_label: "Customer Lifetime"
    value_format_name: percent_1
    sql: ${TABLE}.customer_spend_trend_past_year ;;
  }
}
