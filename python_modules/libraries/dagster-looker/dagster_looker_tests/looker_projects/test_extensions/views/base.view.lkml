view: base {
  sql_table_name: `prod.base_data` ;;
  description: "This is the base view"

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
