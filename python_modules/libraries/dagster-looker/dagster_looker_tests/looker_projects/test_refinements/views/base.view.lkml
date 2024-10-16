view: base {
  sql_table_name: `prod.base_data` ;;

  dimension: email {
    type: string
    sql: ${TABLE}.email ;;
  }

  dimension: name {
    hidden: yes
    type: string
    sql: ${TABLE}.name ;;
  }
}
