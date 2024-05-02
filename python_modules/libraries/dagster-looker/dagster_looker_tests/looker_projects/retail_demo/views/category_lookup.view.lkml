view: category_lookup {
  sql_table_name: `looker-private-demo.retail.category_lookup` ;;

  dimension: category {
    type: string
    sql: ${TABLE}.category ;;
  }

  dimension: category_code {
    type: number
    sql: ${TABLE}.category_code ;;
  }

  dimension: item_code {
    type: number
    sql: ${TABLE}.item_code ;;
  }

  measure: count {
    type: count
    drill_fields: []
  }
}
