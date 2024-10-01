view: channels {
  sql_table_name: `looker-private-demo.retail.channels` ;;

  dimension: id {
    type: number
    hidden: yes
    sql: ${TABLE}.ID ;;
  }

  dimension: name {
    type: string
    label: "Channel Name"
    sql: ${TABLE}.NAME ;;
  }
}
