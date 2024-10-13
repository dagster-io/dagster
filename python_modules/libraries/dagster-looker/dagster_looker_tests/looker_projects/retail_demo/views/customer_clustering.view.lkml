# If necessary, uncomment the line below to include explore_source.
# include: "../models/retail_block_model.model.lkml"

view: customer_clustering_input {
  view_label: "Customers"
  derived_table: {
    explore_source: transactions {
      column: customer_id {}
      column: age { field: customers.age }
      column: total_sales { field: transactions__line_items.total_sales }
      column: total_quantity { field: transactions__line_items.total_quantity }
      column: total_gross_margin { field: transactions__line_items.total_gross_margin }
      column: number_of_transactions {}
      column: average_item_price { field: transactions__line_items.average_item_price }
      column: average_basket_size { field: transactions__line_items.average_basket_size }
      column: first_transaction {}
      filters: [transactions.customer_id: "NOT NULL", stores.name: ""]
    }
  }
}

view: customer_clustering_model {
  derived_table: {
    datagroup_trigger: monthly
    sql_create:
      CREATE OR REPLACE MODEL ${SQL_TABLE_NAME}
      OPTIONS(model_type='kmeans',
        num_clusters=4) AS
      SELECT
         * EXCEPT(customer_id)
      FROM ${customer_clustering_input.SQL_TABLE_NAME};;
  }
}

view: customer_clustering_prediction_base {
  label: "Customer Clusters 👤"
  derived_table: {
    datagroup_trigger: monthly
    sql: SELECT * EXCEPT (nearest_centroids_distance) FROM ml.PREDICT(
      MODEL ${customer_clustering_model.SQL_TABLE_NAME},
      (SELECT * FROM ${customer_clustering_input.SQL_TABLE_NAME}));;
  }
}

view: customer_clustering_prediction_aggregates {
  derived_table: {
    datagroup_trigger: monthly
    sql: SELECT
      CENTROID_ID,
      AVG(age ) AS average_age,
      AVG(average_basket_size ) AS average_basket_size,
      AVG(number_of_transactions ) AS average_number_of_transactions,
      AVG(total_quantity ) AS average_total_quantity,
      AVG(total_sales ) AS average_total_sales,
      COUNT(DISTINCT customer_id) AS customer_count
      FROM ${customer_clustering_prediction_base.SQL_TABLE_NAME}
      GROUP BY 1 ;;
  }
}

view: customer_clustering_prediction_centroid_ranks {
  derived_table: {
    datagroup_trigger: monthly
    sql: SELECT
      centroid_id,
      RANK() OVER (ORDER BY average_age asc) as age_rank,
      RANK() OVER (ORDER BY average_age desc) as inverse_age_rank,
      RANK() OVER (ORDER BY average_basket_size desc) as average_basket_size_rank,
      RANK() OVER (ORDER BY average_total_sales desc) as average_total_sales_rank
      FROM ${customer_clustering_prediction_aggregates.SQL_TABLE_NAME} ;;
  }
}

view: customer_clustering_prediction {
  derived_table: {
    datagroup_trigger: monthly
    sql: SELECT customer_clustering_prediction_base.*
      ,CASE
        WHEN customer_clustering_prediction_centroid_ranks.age_rank = 1 THEN 'Emerging Millennials 🥑'
        WHEN customer_clustering_prediction_centroid_ranks.inverse_age_rank = 1 THEN 'Affluent Retirees 👴'
        WHEN (customer_clustering_prediction_centroid_ranks.average_basket_size_rank = 1 AND customer_clustering_prediction_centroid_ranks.age_rank <> 1 AND customer_clustering_prediction_centroid_ranks.inverse_age_rank <> 1)
          -- OR (customer_clustering_prediction_centroid_ranks.average_total_sales_rank = 1 AND customer_clustering_prediction_centroid_ranks.age_rank <> 1 AND customer_clustering_prediction_centroid_ranks.inverse_age_rank <> 1)
          THEN 'Regular Gen Xers 🛒'
        ELSE 'One-off locals 🏪'
      END AS customer_segment
    FROM ${customer_clustering_prediction_base.SQL_TABLE_NAME} customer_clustering_prediction_base
    JOIN ${customer_clustering_prediction_centroid_ranks.SQL_TABLE_NAME} customer_clustering_prediction_centroid_ranks
      ON customer_clustering_prediction_base.centroid_id = customer_clustering_prediction_centroid_ranks.centroid_id;;
  }

  dimension: centroid_id {
    type: number
    hidden: yes
    sql: ${TABLE}.CENTROID_ID ;;
  }

  dimension: customer_id {
    sql: ${TABLE}.customer_id ;;
  }

  dimension: customer_segment {
    type: string
    sql: ${TABLE}.customer_segment ;;
    order_by_field: centroid_id
    link: {
      url: "/dashboards/rPiqpL214a2t0oOeO58gso?Customer%20Segment={{value | encode_uri}}&Date%20Range={{ _filters['transactions.date_comparison_filter'] | url_encode }}"
      label: "Drill into {{rendered_value}}"
    }
  }

  # Cluster Evaluation

  measure: customer_count {
    type: count_distinct
    sql: ${TABLE}.customer_id ;;
  }

  measure: average_total_sales {
    type: average
    value_format_name: usd
    sql: ${TABLE}.total_sales ;;
  }

  measure: average_age {
    type: average
    value_format_name: decimal_0
    sql: ${TABLE}.age ;;
  }

  measure: average_total_quantity {
    type: average
    value_format_name: usd
    sql: ${TABLE}.total_quantity ;;
  }

  measure: average_number_of_transactions {
    type: average
    value_format_name: decimal_1
    sql: ${TABLE}.number_of_transactions ;;
  }

  measure: average_basket_size {
    type: average
    value_format_name: usd
    sql: ${TABLE}.average_basket_size ;;
  }
}
