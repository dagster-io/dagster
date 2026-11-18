view: order_predictions {
  derived_table: {
    sql:
      SELECT *
      FROM ML.PREDICT(
        MODEL `analytics.order_model`,
        (SELECT * FROM ${orders.SQL_TABLE_NAME})
      ) ;;
  }
}
