view: +base {
  sql_table_name: `prod.new_base_data` ;;

  dimension: name {
    hidden: no
    type: string
    sql: ${TABLE}.name ;;
  }

}
