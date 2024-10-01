view: stock_forecasting_explore_base {
  view_label: "Stock Forecasting 🏭"
  derived_table: {
    explore_source: transactions {
      column: transaction_week {}
      column: transaction_week_of_year {}
      column: product_name { field: products.name }
      column: product_image { field: products.product_image }
      column: department { field: products.department }
      column: category { field: products.category }
      column: brand { field: products.brand }
      column: area { field: products.area }
      column: store_id { field: stores.id }
      column: store_name { field: stores.name }
      column: number_of_customers {}
      column: number_of_transactions {}
      column: number_of_customer_transactions {}
      column: gross_margin { field: transactions__line_items.total_gross_margin }
      column: quantity { field: transactions__line_items.total_quantity }
      column: sales { field: transactions__line_items.total_sales }
      bind_filters: {
        from_field: stock_forecasting_explore_base.transaction_week_filter
        to_field: transactions.transaction_date
      }
    }
  }
  filter: transaction_week_filter { type: date}
  dimension_group: transaction {
    type: time
    timeframes: [week,month,year]
    sql: TIMESTAMP(CAST(${TABLE}.transaction_week AS DATE)) ;;
  }
  dimension: transaction_week_of_year {
    group_label: "Transaction Date"
    type: number
    sql: IFNULL(${transaction_week_of_year_for_join},${stock_forecasting_prediction.transaction_week_of_year}) ;;
  }
  dimension: transaction_week_of_year_for_join {
    hidden: yes
    type: number
    sql:${TABLE}.transaction_week_of_year;;
  }
  dimension: product_name {
    sql: IFNULL(${product_name_for_join},${stock_forecasting_prediction.product_name}) ;;
    link: {
      label: "Drive attachments for {{rendered_value}}"
      icon_url: "https://i.imgur.com/W4tVGrj.png"
      url: "/dashboards/TSGWx3mvSYoyNKLKLDssXW?Focus%20Product={{value | encode_uri}}&Minimum%20Purchase%20Frequency="
    }
  }
  dimension: product_name_for_join {
    hidden: yes
    type: string
    sql:${TABLE}.product_name;;
  }
  dimension: product_image {
    view_label: "Product Detail 📦"
    html: <img src="https://us-central1-looker-private-demo.cloudfunctions.net/imageSearch?q={{value | encode_uri }}" style="height: 50px; max-width: 150px;" /> ;;
  }
  dimension: department {
    view_label: "Product Detail 📦"
  }
  dimension: category {
    view_label: "Product Detail 📦"
  }
  dimension: brand {
    view_label: "Product Detail 📦"
  }
  dimension: area {
    view_label: "Product Detail 📦"
  }
  dimension: store_id {
    hidden: yes
    type: number
    sql: IFNULL(${store_id_for_join},${stock_forecasting_prediction.store_id}) ;;
  }
  dimension: store_id_for_join {
    hidden: yes
    type: number
    sql: ${TABLE}.store_id ;;
  }
  dimension: store_name {}
  dimension: number_of_customers {
    value_format: "#,##0"
    type: number
  }
  dimension: number_of_transactions {
    value_format: "#,##0"
    type: number
  }
  dimension: number_of_customer_transactions {
    value_format: "#,##0"
    type: number
  }
  dimension: gross_margin {
    label: "Transactions Gross Margin"
    value_format: "$#,##0"
    type: number
  }
  dimension: quantity {
    label: "Transactions Quantity"
    value_format: "#,##0"
    type: number
  }
  dimension: sales {
    label: "Transactions Sales"
    value_format: "$#,##0"
    type: number
  }

  ##### DERIVED DIMENSIONS #####

  set: drill_detail {
    fields: [transaction_week, store_id, product_name, total_quantity]
  }

  ##### MEASURES #####

  measure: total_number_of_transactions {
    type: sum
    sql: ${number_of_transactions} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: total_number_of_customer_transactions {
    hidden: yes
    type: sum
    sql: ${number_of_customer_transactions} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: total_number_of_customers {
    type: sum
    sql: ${number_of_customers} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: percent_customer_transactions {
    type: number
    sql: ${number_of_customer_transactions}/NULLIF(${number_of_transactions},0) ;;
    value_format_name: percent_1
    drill_fields: [drill_detail*]
  }

  measure: total_sales {
    type: sum
    sql: ${sales} ;;
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
    label: "Total Stock"
    type: sum
    sql: ${quantity} ;;
    value_format_name: decimal_0
    drill_fields: [drill_detail*]
  }

  measure: average_basket_size {
    type: number
    sql: ${total_sales}/NULLIF(${total_number_of_transactions},0) ;;
    value_format_name: usd
    drill_fields: [drill_detail*]
  }

  measure: average_item_price {
    type: number
    sql: ${total_sales}/NULLIF(${total_quantity},0) ;;
    value_format_name: usd
    drill_fields: [transactions.drill_detail*]
  }

  measure: stock_difference {
    type: number
    sql: ${stock_forecasting_prediction.forecasted_quantity}-${total_quantity} ;;
    value_format_name: decimal_0
  }

  measure: stock_difference_value {
    type: number
    sql: ${stock_difference}*${average_item_price} ;;
    value_format_name: usd
  }
}

view: stock_forecasting_product_store_week_facts {
  derived_table: {
    explore_source: transactions {
      column: transaction_week_of_year {}
      column: id { field: stores.id }
      column: name { field: products.name }
      column: category { field: products.category }
      column: total_quantity { field: transactions__line_items.total_quantity }
      column: store_size_grouping { field: stores.store_size_grouping }
      column: sq_ft { field: stores.sq_ft }
      filters: {
        field: transactions.transaction_date
        value: "1 years ago for 1 years"
      }
    }
  }
  dimension: transaction_week_of_year {}
  dimension: id {}
  dimension: name {}
  dimension: category {}
  dimension: total_quantity {}
  dimension: store_size_grouping {}
  dimension: sq_ft {}
}

view: stock_forecasting_product_store_week_facts_prior_year {
  derived_table: {
    explore_source: transactions {
      column: transaction_week_of_year {}
      column: id { field: stores.id }
      column: name { field: products.name }
      column: total_quantity { field: transactions__line_items.total_quantity }
      column: average_basket_size { field: transactions__line_items.average_basket_size }
      column: average_item_price { field: transactions__line_items.average_item_price }
      column: total_sales { field: transactions__line_items.total_sales }
      column: total_gross_margin { field: transactions__line_items.total_gross_margin }
      column: percent_customer_transactions {}
      column: number_of_transactions {}
      column: number_of_customers {}
      filters: {
        field: transactions.transaction_date
        value: "2 years ago for 1 years"
      }
    }
  }
  dimension: transaction_week_of_year {}
  dimension: id {}
  dimension: name {}
  dimension: total_quantity {}
  dimension: average_basket_size {}
  dimension: average_item_price {}
  dimension: total_sales {}
  dimension: total_gross_margin {}
  dimension: percent_customer_transactions {}
  dimension: number_of_transactions {}
  dimension: number_of_customers {}
}

view: stock_forecasting_store_week_facts_prior_year {
  derived_table: {
    explore_source: transactions {
      column: transaction_week_of_year {}
      column: id { field: stores.id }
      column: name { field: products.name }
      column: total_quantity { field: transactions__line_items.total_quantity }
      column: average_basket_size { field: transactions__line_items.average_basket_size }
      column: average_item_price { field: transactions__line_items.average_item_price }
      column: average_daily_precipitation { field: store_weather.average_daily_precipitation }
      column: average_max_temparature { field: store_weather.average_max_temparature }
      column: average_min_temparature { field: store_weather.average_min_temparature }
      column: total_sales { field: transactions__line_items.total_sales }
      column: total_gross_margin { field: transactions__line_items.total_gross_margin }
      column: percent_customer_transactions {}
      column: number_of_transactions {}
      column: number_of_customers {}
      filters: {
        field: transactions.transaction_date
        value: "2 years ago for 1 years"
      }
    }
  }
  dimension: transaction_week_of_year {}
  dimension: id {}
  dimension: name {}
  dimension: total_quantity {}
  dimension: average_basket_size {}
  dimension: average_item_price {}
  dimension: average_daily_precipitation {}
  dimension: average_max_temparature {}
  dimension: average_min_temparature {}
  dimension: total_sales {}
  dimension: total_gross_margin {}
  dimension: percent_customer_transactions {}
  dimension: number_of_transactions {}
  dimension: number_of_customers {}
}

view: stock_forecasting_category_week_facts_prior_year {
  derived_table: {
    explore_source: transactions {
      column: transaction_week_of_year {}
      column: category { field: products.category }
      column: total_quantity { field: transactions__line_items.total_quantity }
      column: average_basket_size { field: transactions__line_items.average_basket_size }
      column: average_item_price { field: transactions__line_items.average_item_price }
      column: total_sales { field: transactions__line_items.total_sales }
      column: total_gross_margin { field: transactions__line_items.total_gross_margin }
      column: percent_customer_transactions {}
      column: number_of_transactions {}
      column: number_of_customers {}
      filters: {
        field: transactions.transaction_date
        value: "2 years ago for 1 years"
      }
    }
  }
  dimension: transaction_week_of_year {}
  dimension: category {}
  dimension: total_quantity {}
  dimension: average_basket_size {}
  dimension: average_item_price {}
  dimension: total_sales {}
  dimension: total_gross_margin {}
  dimension: percent_customer_transactions {}
  dimension: number_of_transactions {}
  dimension: number_of_customers {}
}

explore: stock_forecasting_product_store_week_facts {
  hidden: yes
  join: stock_forecasting_product_store_week_facts_prior_year {
    relationship: one_to_one
    sql_on: ${stock_forecasting_product_store_week_facts.transaction_week_of_year} = ${stock_forecasting_product_store_week_facts_prior_year.transaction_week_of_year}
    AND ${stock_forecasting_product_store_week_facts.id} = ${stock_forecasting_product_store_week_facts_prior_year.id}
    AND ${stock_forecasting_product_store_week_facts.name} = ${stock_forecasting_product_store_week_facts_prior_year.name};;
  }
  join: stock_forecasting_store_week_facts_prior_year {
    relationship: many_to_one
    sql_on: ${stock_forecasting_product_store_week_facts.transaction_week_of_year} = ${stock_forecasting_store_week_facts_prior_year.transaction_week_of_year}
          AND ${stock_forecasting_product_store_week_facts.id} = ${stock_forecasting_store_week_facts_prior_year.id};;
  }
  join: stock_forecasting_category_week_facts_prior_year {
    relationship: many_to_one
    sql_on: ${stock_forecasting_product_store_week_facts.transaction_week_of_year} = ${stock_forecasting_category_week_facts_prior_year.transaction_week_of_year}
      AND ${stock_forecasting_product_store_week_facts.category} = ${stock_forecasting_category_week_facts_prior_year.category};;
  }
}

###########################################################################################
###################################  BEGIN BQML MODEL  ####################################
###########################################################################################

view: stock_forecasting_input {
  derived_table: {
    explore_source: stock_forecasting_product_store_week_facts {
      column: transaction_week_of_year {}
      column: store_id { field: stock_forecasting_product_store_week_facts.id}
      column: product_name { field: stock_forecasting_product_store_week_facts.name }
      column: category {}
      column: sq_ft {}
      column: store_size_grouping {}
      column: total_quantity {}
      column: stock_forecasting_category_week_facts_prior_year__average_basket_size { field: stock_forecasting_category_week_facts_prior_year.average_basket_size }
      column: stock_forecasting_category_week_facts_prior_year__average_item_price { field: stock_forecasting_category_week_facts_prior_year.average_item_price }
      column: stock_forecasting_category_week_facts_prior_year__number_of_customers { field: stock_forecasting_category_week_facts_prior_year.number_of_customers }
      column: stock_forecasting_category_week_facts_prior_year__number_of_transactions { field: stock_forecasting_category_week_facts_prior_year.number_of_transactions }
      column: stock_forecasting_category_week_facts_prior_year__percent_customer_transactions { field: stock_forecasting_category_week_facts_prior_year.percent_customer_transactions }
      column: stock_forecasting_category_week_facts_prior_year__total_gross_margin { field: stock_forecasting_category_week_facts_prior_year.total_gross_margin }
      column: stock_forecasting_category_week_facts_prior_year__total_quantity { field: stock_forecasting_category_week_facts_prior_year.total_quantity }
      column: stock_forecasting_category_week_facts_prior_year__total_sales { field: stock_forecasting_category_week_facts_prior_year.total_sales }
      column: stock_forecasting_product_store_week_facts_prior_year__average_basket_size { field: stock_forecasting_product_store_week_facts_prior_year.average_basket_size }
      column: stock_forecasting_product_store_week_facts_prior_year__average_item_price { field: stock_forecasting_product_store_week_facts_prior_year.average_item_price }
      column: stock_forecasting_product_store_week_facts_prior_year__number_of_customers { field: stock_forecasting_product_store_week_facts_prior_year.number_of_customers }
      column: stock_forecasting_product_store_week_facts_prior_year__number_of_transactions { field: stock_forecasting_product_store_week_facts_prior_year.number_of_transactions }
      column: stock_forecasting_product_store_week_facts_prior_year__percent_customer_transactions { field: stock_forecasting_product_store_week_facts_prior_year.percent_customer_transactions }
      column: stock_forecasting_product_store_week_facts_prior_year__total_gross_margin { field: stock_forecasting_product_store_week_facts_prior_year.total_gross_margin }
      column: stock_forecasting_product_store_week_facts_prior_year__total_quantity { field: stock_forecasting_product_store_week_facts_prior_year.total_quantity }
      column: stock_forecasting_product_store_week_facts_prior_year__total_sales { field: stock_forecasting_product_store_week_facts_prior_year.total_sales }
      column: stock_forecasting_store_week_facts_prior_year__average_basket_size { field: stock_forecasting_store_week_facts_prior_year.average_basket_size }
      column: stock_forecasting_store_week_facts_prior_year__average_daily_precipitation { field: stock_forecasting_store_week_facts_prior_year.average_daily_precipitation }
      column: stock_forecasting_store_week_facts_prior_year__average_item_price { field: stock_forecasting_store_week_facts_prior_year.average_item_price }
      column: stock_forecasting_store_week_facts_prior_year__average_max_temparature { field: stock_forecasting_store_week_facts_prior_year.average_max_temparature }
      column: stock_forecasting_store_week_facts_prior_year__average_min_temparature { field: stock_forecasting_store_week_facts_prior_year.average_min_temparature }
      column: stock_forecasting_store_week_facts_prior_year__number_of_customers { field: stock_forecasting_store_week_facts_prior_year.number_of_customers }
      column: stock_forecasting_store_week_facts_prior_year__number_of_transactions { field: stock_forecasting_store_week_facts_prior_year.number_of_transactions }
      column: stock_forecasting_store_week_facts_prior_year__percent_customer_transactions { field: stock_forecasting_store_week_facts_prior_year.percent_customer_transactions }
      column: stock_forecasting_store_week_facts_prior_year__total_gross_margin { field: stock_forecasting_store_week_facts_prior_year.total_gross_margin }
      column: stock_forecasting_store_week_facts_prior_year__total_quantity { field: stock_forecasting_store_week_facts_prior_year.total_quantity }
      column: stock_forecasting_store_week_facts_prior_year__total_sales { field: stock_forecasting_store_week_facts_prior_year.total_sales }
    }
  }
}

view: stock_forecasting_regression {
  derived_table: {
    datagroup_trigger: weekly
    sql_create:
      CREATE OR REPLACE MODEL ${SQL_TABLE_NAME}
      OPTIONS(model_type='linear_reg'
        , labels=['total_quantity']
        , min_rel_progress = 0.05
        , max_iteration = 50
        ) AS
      SELECT
         * EXCEPT(transaction_week_of_year, store_id, product_name)
      FROM ${stock_forecasting_input.SQL_TABLE_NAME};;
  }
}

view: stock_forecasting_prediction {
  derived_table: {
    sql: SELECT transaction_week_of_year,store_id,product_name
        ,CONCAT(CAST(transaction_week_of_year AS STRING),'_',CAST(store_id AS STRING),product_name) AS pk
        ,category
        ,predicted_total_quantity
      FROM ml.PREDICT(
      MODEL ${stock_forecasting_regression.SQL_TABLE_NAME},
      (SELECT * FROM ${stock_forecasting_input.SQL_TABLE_NAME}));;
    datagroup_trigger: weekly
  }

  dimension: pk {
    hidden: yes
    primary_key: yes
    type: string
    sql: ${TABLE}.pk ;;
  }

  dimension: transaction_week_of_year {
    hidden: yes
    type: number
    sql: ${TABLE}.transaction_week_of_year ;;
  }

  dimension: store_id {
    hidden: yes
    type: number
    sql: ${TABLE}.store_id ;;
  }

  dimension: product_name {
    hidden: yes
    type: string
    sql: ${TABLE}.product_name ;;
  }

  dimension: category {
    hidden: yes
    type: string
    sql: ${TABLE}.category ;;
  }

  dimension: predicted_total_quantity {
    hidden: yes
    type: number
    sql: ${TABLE}.predicted_total_quantity ;;
  }

  dimension: predicted_total_quantity_rounded {
    hidden: yes
    type: number
    sql: ROUND(${predicted_total_quantity},0) ;;
  }

  measure: forecasted_quantity {
    view_label: "Stock Forecasting 🏭"
    label: "Forecasted Stock 📈"
    type: sum
    sql: ${predicted_total_quantity_rounded} ;;
    value_format_name: decimal_0
  }
}
