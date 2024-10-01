view: customer_transaction_sequence {
  # TO DO: replace with reference to NDT
  derived_table: {
    sql: SELECT customer_id, transaction_timestamp, category_list, transaction_sequence
        ,MIN(CASE WHEN transaction_sequence=1 THEN category_list ELSE NULL END) OVER (PARTITION BY customer_id) AS category_list_transaction_1
        ,MIN(CASE WHEN transaction_sequence=2 THEN category_list ELSE NULL END) OVER (PARTITION BY customer_id) AS category_list_transaction_2
        ,MIN(CASE WHEN transaction_sequence=3 THEN category_list ELSE NULL END) OVER (PARTITION BY customer_id) AS category_list_transaction_3
        ,MIN(CASE WHEN transaction_sequence=4 THEN category_list ELSE NULL END) OVER (PARTITION BY customer_id) AS category_list_transaction_4
        ,MIN(CASE WHEN transaction_sequence=5 THEN category_list ELSE NULL END) OVER (PARTITION BY customer_id) AS category_list_transaction_5
        ,MIN(CASE WHEN transaction_sequence=1 THEN main_category ELSE NULL END) OVER (PARTITION BY customer_id) AS main_category_transaction_1
        ,MIN(CASE WHEN transaction_sequence=2 THEN main_category ELSE NULL END) OVER (PARTITION BY customer_id) AS main_category_transaction_2
        ,MIN(CASE WHEN transaction_sequence=3 THEN main_category ELSE NULL END) OVER (PARTITION BY customer_id) AS main_category_transaction_3
        ,MIN(CASE WHEN transaction_sequence=4 THEN main_category ELSE NULL END) OVER (PARTITION BY customer_id) AS main_category_transaction_4
        ,MIN(CASE WHEN transaction_sequence=5 THEN main_category ELSE NULL END) OVER (PARTITION BY customer_id) AS main_category_transaction_5
       FROM
       (SELECT customer_id, transaction_timestamp, main_category, category_list
        , DENSE_RANK() OVER (PARTITION BY customer_id ORDER BY transaction_timestamp ASC) AS transaction_sequence
        FROM
        (SELECT transactions.customer_id, transactions.transaction_timestamp
          , STRING_AGG(products.category, ", " ORDER BY line_items.sale_price desc LIMIT 1) as main_category
          , STRING_AGG(distinct products.category, ", " ORDER BY products.category asc) as category_list
        FROM ${transactions.SQL_TABLE_NAME} transactions
        LEFT JOIN UNNEST(transactions.line_items) line_items
        LEFT JOIN ${products.SQL_TABLE_NAME}  AS products
          ON line_items.product_id = products.ID
        WHERE {% condition transactions.transaction_date %} transaction_timestamp {% endcondition %}
        GROUP BY 1,2));;
  }

  dimension: customer_id {
    hidden: yes
    type: number
    sql: ${TABLE}.customer_id ;;
  }

  dimension_group: transaction {
    hidden: yes
    type: time
    timeframes: [raw,date]
    sql: ${TABLE}.transaction_timestamp ;;
  }

  dimension: category_list {
    type: string
    sql: ${TABLE}.category_list ;;
  }

  dimension: transaction_sequence {
    type: number
    sql: ${TABLE}.transaction_sequence ;;
  }

  dimension: product_category_list_transaction_1 {
    type: string
    sql: ${TABLE}.category_list_transaction_1 ;;
  }

  dimension: product_category_list_transaction_2 {
    type: string
    sql: ${TABLE}.category_list_transaction_2 ;;
  }

  dimension: product_category_list_transaction_3 {
    type: string
    sql: ${TABLE}.category_list_transaction_3 ;;
  }

  dimension: product_category_list_transaction_4 {
    type: string
    sql: ${TABLE}.category_list_transaction_4 ;;
  }

  dimension: product_category_list_transaction_5 {
    type: string
    sql: ${TABLE}.category_list_transaction_5 ;;
  }

  dimension: main_product_category_transaction_1 {
    type: string
    sql: ${TABLE}.main_category_transaction_1 ;;
  }

  dimension: main_product_category_transaction_2 {
    type: string
    sql: ${TABLE}.main_category_transaction_2 ;;
  }

  dimension: main_product_category_transaction_3 {
    type: string
    sql: ${TABLE}.main_category_transaction_3 ;;
  }

  dimension: main_product_category_transaction_4 {
    type: string
    sql: ${TABLE}.main_category_transaction_4 ;;
  }

  dimension: main_product_category_transaction_5 {
    type: string
    sql: ${TABLE}.main_category_transaction_5 ;;
  }
}
