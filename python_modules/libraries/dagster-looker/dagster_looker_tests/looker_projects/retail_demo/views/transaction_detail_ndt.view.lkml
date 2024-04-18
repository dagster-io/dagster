#### Keeping in case helps with block, otherwise delete view as no longer used

include: "date_comparison.view.lkml"

view: transaction_detail {
  derived_table: {
    explore_source: transactions {
      column: transaction_id {}
      column: customer_id {}
      column: channel_id {}
      column: gross_margin { field: transactions__line_items.gross_margin }
      column: product_id { field: transactions__line_items.product_id }
      column: store_id {}
      column: sale_price { field: transactions__line_items.sale_price }
      column: transaction_raw {}
      column: latitude { field: stores.latitude }
      column: longitude { field: stores.longitude }
      column: store_name { field: stores.name }
      column: store_state { field: stores.state }
      column: store_sq_ft { field: stores.sq_ft }
      column: brand { field: products.brand }
      column: category { field: products.category }
      column: department { field: products.department }
      column: area { field: products.area }
      column: product_name { field: products.name }
      column: sku { field: products.sku }
      column: channel_name { field: channels.name }
      column: traffic_source { field: customers.traffic_source }
      column: city { field: customers.city }
      column: country { field: customers.country }
      column: registered_date { field: customers.registered_date }
      column: email { field: customers.email }
      column: first_name { field: customers.first_name }
      column: gender { field: customers.gender }
      column: last_name { field: customers.last_name }
      column: address_latitude { field: customers.latitude }
      column: address_longitude { field: customers.longitude }
      column: state { field: customers.state }
      column: postcode { field: customers.postcode }
      column: customer_average_basket_size { field: customer_facts.customer_average_basket_size }
      column: customer_lifetime_gross_margin { field: customer_facts.customer_lifetime_gross_margin }
      column: customer_lifetime_sales { field: customer_facts.customer_lifetime_sales }
      column: customer_lifetime_transactions { field: customer_facts.customer_lifetime_transactions }
      column: customer_lifetime_quantity { field: customer_facts.customer_lifetime_quantity }
      column: customer_first_purchase_date { field: customer_facts.customer_first_purchase_date }
    }
#     datagroup_trigger: daily
#     partition_keys: ["transaction_raw"]
#     cluster_keys: ["store_name"]
  }


  dimension: transaction_id {type: number}
  dimension: customer_id {type: number hidden: yes}
  dimension: channel_id {type: number hidden: yes}
  dimension: product_id {type: number hidden: yes}
  dimension: store_id {type: number hidden: yes}
  dimension: sale_price {type: number}
  dimension: gross_margin {type: number}
  dimension_group: transaction {
    type: time
    sql: ${TABLE}.transaction_raw ;;
  }
  dimension: latitude {
    view_label: "Store"
    type: number
    hidden: yes
  }
  dimension: longitude {
    view_label: "Store"
    type: number
    hidden: yes
  }
  dimension: store_name {view_label: "Store"}
  dimension: store_state {view_label: "Store"}
  dimension: store_sq_ft {view_label: "Store" type: number}
  dimension: brand {view_label: "Product"}  # Optional
  dimension: category {view_label: "Product"}
  dimension: department {view_label: "Product"}  # Optional
  dimension: area {view_label: "Product"}  # Optional
  dimension: product_name {view_label: "Product"}
  dimension: sku {view_label: "Product"}  # Optional
  dimension: channel_name {view_label: "Channel"}
  dimension: traffic_source {view_label: "Customer"}  # Optional
  dimension: city {view_label: "Customer"}  # Optional
  dimension: country {view_label: "Customer"}
  dimension_group: registered {
    view_label: "Customer"
    type: time
    timeframes: [raw,date,week,month,year,day_of_week,week_of_year,month_name,quarter,quarter_of_year]
    sql: ${TABLE}.registered_date ;;
  }
  dimension: email {view_label: "Customer"}  # Optional
  dimension: first_name {view_label: "Customer"}  # Optional
  dimension: gender {view_label: "Customer"}  # Optional
  dimension: last_name {view_label: "Customer"}  # Optional
  dimension: address_latitude {
    view_label: "Customer"
    type: number
  }  # Optional
  dimension: address_longitude {
    view_label: "Customer"
    type: number
  }  # Optional
  dimension: state {view_label: "Customer"}  # Optional
  dimension: postcode {
    view_label: "Customer"
    type: zipcode
  }
  dimension: customer_average_basket_size { type: number view_label: "Customer" }
  dimension: customer_lifetime_gross_margin { type: number view_label: "Customer" }
  dimension: customer_lifetime_sales { type: number view_label: "Customer" }
  dimension: customer_lifetime_transactions { type: number view_label: "Customer" }
  dimension: customer_lifetime_quantity { type: number view_label: "Customer" }
  dimension_group: customer_first_purchase { type: time timeframes:[raw,date,week,month] view_label: "Customer" }

  ##### DERIVED DIMENSIONS #####

  set: drill_detail {
    fields: [transaction_date,store_name, category, total_sales]
  }

  extends: [date_comparison]

    ##### Product Hierarchy #####

    ##### Stores #####

  dimension: store_location {
    view_label: "Store"
    type: location
    sql_latitude: ${latitude} ;;
    sql_longitude: ${longitude} ;;
  }

  dimension: store_size_grouping {
    view_label: "Store"
    type: string
    sql: CASE
      WHEN ${store_sq_ft} <= 70000 THEN 'S'
      WHEN ${store_sq_ft} <= 100000 THEN 'M'
      WHEN ${store_sq_ft} <= 130000 THEN 'L'
      WHEN ${store_sq_ft} <= 160000 THEN 'XL'
    END ;;
    order_by_field: store_size_grouping_order
  }

  dimension: store_size_grouping_order {
    view_label: "Store"
    hidden: yes
    type: number
    sql: CASE ${store_size_grouping}
      WHEN 'S' THEN 1
      WHEN 'M' THEN 2
      WHEN 'L' THEN 3
      WHEN 'XL' THEN 4
    END
    ;;
  }


  ##### MEASURES #####

  measure: number_of_transactions {
    type: count_distinct
    sql: ${transaction_id} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: number_of_customers {
    type: count_distinct
    sql: ${customer_id} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: number_of_stores {
    view_label: "Store"
    type: count_distinct
    sql: ${store_id} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: total_sales {
    type: sum
    sql: ${sale_price} ;;
    value_format_name: usd_0
    drill_fields: [drill_detail*]
  }

  measure: total_gross_margin {
    type: sum
    sql: ${gross_margin} ;;
    value_format_name: usd_0
    drill_fields: [drill_detail*]
  }

  measure: total_quantity {
    type: sum
    sql: 1 ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: average_basket_size {
    type: number
    sql: ${total_sales}/NULLIF(${number_of_transactions},0) ;;
    value_format_name: usd
    drill_fields: [drill_detail*]
  }

  measure: average_item_price {
    type: number
    sql: ${total_sales}/NULLIF(${total_quantity},0) ;;
    value_format_name: usd
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
}
