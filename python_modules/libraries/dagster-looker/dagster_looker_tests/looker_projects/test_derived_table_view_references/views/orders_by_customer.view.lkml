view: orders_by_customer {
  derived_table: {
    sql:
      SELECT
        customers.id AS customer_id,
        COUNT(*) AS order_count
      FROM ${orders.SQL_TABLE_NAME} AS orders
      JOIN raw.customers AS customers ON customers.id = orders.customer_id
      GROUP BY 1 ;;
  }
}
