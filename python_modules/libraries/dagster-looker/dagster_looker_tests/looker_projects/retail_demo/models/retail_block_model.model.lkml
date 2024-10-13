connection: "looker-private-demo"
label: "Retail"

include: "/views/**/*.view" # include all the views
include: "/dashboards/*.dashboard.lookml" # include all the dashboards


explore: transactions {
  label: "(1) Transaction Detail 🏷"
  always_filter: {
    filters: {
      field: transaction_date
      value: "last 30 days"
    }
  }

  access_filter: {
    field: stores.name
    user_attribute: store
  }

  join: transactions__line_items {
    relationship: one_to_many
    sql: LEFT JOIN UNNEST(${transactions.line_items}) transactions__line_items ;;
  }

  join: customers {
    relationship: many_to_one
    sql_on: ${transactions.customer_id} = ${customers.id} ;;
  }

  join: customer_facts {
    relationship: many_to_one
    view_label: "Customers"
    sql_on: ${transactions.customer_id} = ${customer_facts.customer_id} ;;
  }

  join: products {
    relationship: many_to_one
    sql_on: ${products.id} = ${transactions__line_items.product_id} ;;
  }

  join: stores {
    type: left_outer
    sql_on: ${stores.id} = ${transactions.store_id} ;;
    relationship: many_to_one
  }

  join: channels {
    type: left_outer
    view_label: "Transactions"
    sql_on: ${channels.id} = ${transactions.channel_id} ;;
    relationship: many_to_one
  }

  join: customer_transaction_sequence {
    relationship: many_to_one
    sql_on: ${transactions.customer_id} = ${customer_transaction_sequence.customer_id}
      AND ${transactions.transaction_raw} = ${customer_transaction_sequence.transaction_raw} ;;
  }

  join: store_weather {
    relationship: many_to_one
    sql_on: ${transactions.transaction_date} = ${store_weather.weather_date}
      AND ${transactions.store_id} = ${store_weather.store_id};;
  }

  join: customer_clustering_prediction {
    fields: [customer_clustering_prediction.centroid_id,customer_clustering_prediction.customer_segment]
    view_label: "Customers"
    relationship: many_to_one
    sql_on: ${transactions.customer_id} = ${customer_clustering_prediction.customer_id} ;;
  }

  sql_always_where: {% if transactions.comparison_type._is_filtered %}
    {% if transactions.comparison_type._parameter_value == 'year' %}
    {% condition transactions.date_comparison_filter %} ${transaction_raw} {% endcondition %} OR (${transaction_raw} >= TIMESTAMP(DATE_ADD(CAST({% date_start transactions.date_comparison_filter %} AS DATE),INTERVAL -1 YEAR)) AND ${transaction_raw} <= TIMESTAMP(DATE_ADD(CAST({% date_end transactions.date_comparison_filter %} AS DATE),INTERVAL -365 DAY)))
    {% elsif transactions.comparison_type._parameter_value == 'week' %}
    {% condition transactions.date_comparison_filter %} ${transaction_raw} {% endcondition %} OR (${transaction_raw} >= TIMESTAMP(DATE_ADD(CAST({% date_start transactions.date_comparison_filter %} AS DATE),INTERVAL -1 WEEK)) AND ${transaction_raw} <= TIMESTAMP(DATE_ADD(CAST({% date_end transactions.date_comparison_filter %} AS DATE),INTERVAL -6 DAY)))
    {% elsif transactions.comparison_type._parameter_value == 'YTD' %}
    EXTRACT(YEAR FROM ${transaction_date}) = EXTRACT(YEAR FROM CURRENT_DATE()) OR EXTRACT(YEAR FROM ${transaction_date}) = EXTRACT(YEAR FROM DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)) AND ${transaction_date} <= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    {% elsif transactions.comparison_type._parameter_value == 'WTD' %}
    DATE_TRUNC(${transaction_date}, WEEK(MONDAY)) = DATE_TRUNC(CURRENT_DATE() , WEEK(MONDAY)) OR (EXTRACT(WEEK FROM ${transaction_date}) = EXTRACT(WEEK FROM DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)) AND ${transaction_date} <= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY))

   {% else %}
    1=1
    {% endif %}
  {% else %}
  1=1
  {% endif %};;
}

explore: stock_forecasting_explore_base {
  label: "(2) Stock Forecasting 🏭"

  always_filter: {
    filters: {
      field: transaction_week_filter
      value: "last 12 weeks"
    }
  }

  join: stock_forecasting_prediction {
    relationship: one_to_one
    type: full_outer
    sql_on: ${stock_forecasting_explore_base.transaction_week_of_year_for_join} = ${stock_forecasting_prediction.transaction_week_of_year}
          AND ${stock_forecasting_explore_base.store_id_for_join} = ${stock_forecasting_prediction.store_id}
          AND ${stock_forecasting_explore_base.product_name_for_join} = ${stock_forecasting_prediction.product_name};;
  }
}

explore: order_purchase_affinity {
  label: "(3) Item Affinity 🔗"
  view_label: "Item Affinity"

  always_filter: {
    filters: {
      field: affinity_timeframe
      value: "last 90 days"
    }
    filters: {
      field: order_items_base.product_level
      value: "product"
    }
  }

  join: order_items_base {}

  join: total_orders {
    type: cross
    relationship: many_to_one
  }
}

explore: customer_clustering_prediction {
  label: "(4) Customer Segments 👤"
  join: transactions {
    # to avoid warning on dashboard URL link in customer_segment dimension
    fields: [transactions.date_comparison_filter]
  }
}

### caching

datagroup: daily {
  sql_trigger: SELECT CURRENT_DATE() ;;
  max_cache_age: "24 hours"
}

datagroup: weekly {
  sql_trigger: SELECT EXTRACT(WEEK FROM CURRENT_DATE()) ;;
}

datagroup: monthly {
  sql_trigger: SELECT EXTRACT(MONTH FROM CURRENT_DATE()) ;;
}
