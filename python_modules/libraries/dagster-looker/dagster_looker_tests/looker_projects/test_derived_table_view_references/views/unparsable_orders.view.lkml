view: unparsable_orders {
  derived_table: {
    sql:
      SELECT *
      FROM ${orders.SQL_TABLE_NAME}
      WHERE (status = "complete" ;;
  }
}
