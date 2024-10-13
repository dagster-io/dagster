view: retail_clv_predict {
  sql_table_name: `retail_ltv.lpd_retail_clv_predict_tbl` ;;
  drill_fields: [customer_id]

  dimension: customer_id {
    primary_key: yes
    type: number
    sql: ${TABLE}.id ;;
  }

  dimension: email {
    type: string
    sql: ${TABLE}.email ;;
  }

  dimension: first_name {
    type: string
    sql: ${TABLE}.first_name ;;
  }

  dimension: last_name {
    type: string
    sql: ${TABLE}.last_name ;;
  }

  dimension: monetary_future {
    type: number
    sql: ${TABLE}.monetary_future ;;
  }

  dimension: monetary_so_far {
    type: number
    sql: ${TABLE}.monetary_so_far ;;
  }

  dimension: predicted_clv {
    alias: [c360.predicted_clv]
    value_format:"[>=1000000]$0.0,,\"M\";[>=1000]$0.0,\"K\";$0.0"
    label: "Predicted CLV"
    type: number
    sql: ${TABLE}.monetary_predicted ;;
  }

  measure: average_clv {
    alias: [c360.average_clv]
    value_format:"[>=1000000]$0.0,,\"M\";[>=1000]$0.0,\"K\";$0.0"
    label: "Average CLV"
    type: average
    sql: ${predicted_clv} ;;
  }
}
