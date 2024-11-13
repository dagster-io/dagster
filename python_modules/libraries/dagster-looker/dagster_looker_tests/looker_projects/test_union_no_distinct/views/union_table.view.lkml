view: union_table {
  derived_table: {
    sql:
      SELECT
        *
      FROM (
        select * from `looker-private-demo.retail.us_stores`
        UNION
        select * from `looker-private-demo.retail.eu_stores`
      ) ;;
  }
}
