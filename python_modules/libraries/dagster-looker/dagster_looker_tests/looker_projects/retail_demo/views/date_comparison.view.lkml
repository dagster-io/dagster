view: date_comparison {
  extension: required

  filter: date_comparison_filter {
    view_label: "Date Comparison"
    type: date
  }

  parameter: comparison_type {
    view_label: "Date Comparison"
    type: unquoted
    allowed_value: {
      label: "Year"
      value: "year"
    }
    allowed_value: {
      label: "Week"
      value: "week"
    }
    allowed_value: {
      label: "YTD"
      value: "YTD"
    }
    allowed_value: {
      label: "WTD"
      value: "WTD"
    }
    default_value: "year"
  }

  dimension: selected_comparison {
    view_label: "Date Comparison"
    sql: {% if comparison_type._parameter_value == "year" %}
    ${this_year_vs_last_year}
    {% elsif comparison_type._parameter_value == "week" %}
    ${this_week_vs_last_week}
    {% elsif comparison_type._parameter_value == "YTD" %}
    ${ytd_vs_lytd}
    {% elsif comparison_type._parameter_value == "WTD" %}
    ${wtd_vs_lwtd}
    {% else %}
    0
    {% endif %};;
  }

  dimension: this_year_vs_last_year {
    hidden: yes
    view_label: "Date Comparison"
    type: string
    sql: CASE
      WHEN {% condition date_comparison_filter %} ${transaction_raw} {% endcondition %} THEN 'This Year'
      WHEN ${transaction_raw} >= TIMESTAMP(DATE_ADD(CAST({% date_start date_comparison_filter %} AS DATE), INTERVAL -1 YEAR)) AND ${transaction_raw} <= TIMESTAMP(DATE_ADD(CAST({% date_end date_comparison_filter %} AS DATE), INTERVAL -365 DAY)) THEN 'Prior Year'
    END;;
  }

  dimension: this_week_vs_last_week {
    hidden: yes
    view_label: "Date Comparison"
    type: string
    sql: CASE
      WHEN {% condition date_comparison_filter %} ${transaction_raw} {% endcondition %} THEN 'This Week'
      WHEN ${transaction_raw} >= TIMESTAMP(DATE_ADD(CAST({% date_start date_comparison_filter %} AS DATE), INTERVAL -1 WEEK)) AND ${transaction_raw} < TIMESTAMP(DATE_ADD(CAST({% date_end date_comparison_filter %} AS DATE), INTERVAL -1 WEEK)) THEN 'Prior Week'
    END;;
  }
  dimension: ytd_vs_lytd {
    hidden: yes
    view_label: "Date Comparison"
    type: string
    sql: CASE
      WHEN EXTRACT(YEAR FROM ${transaction_date}) = EXTRACT(YEAR FROM CURRENT_DATE()) THEN 'This YTD'
      WHEN EXTRACT(YEAR FROM ${transaction_date}) = EXTRACT(YEAR FROM DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)) AND ${transaction_date} <= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY) THEN 'Prior YTD'
    END;;
  }

  dimension: wtd_vs_lwtd {
    hidden: yes
    view_label: "Date Comparison"
    type: string
    sql: CASE
      WHEN DATE_TRUNC(${transaction_date}, WEEK(MONDAY)) = DATE_TRUNC(CURRENT_DATE() , WEEK(MONDAY)) THEN 'This WTD'
      WHEN EXTRACT(WEEK FROM ${transaction_date}) = EXTRACT(WEEK FROM DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)) AND ${transaction_date} <= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY) THEN 'Prior Year WTD'
    END;;

  }
  # dimension: wtd_vs_lywtd {
  #   hidden: yes
  #   view_label: "Date Comparison"
  #   type: string
  #   sql: CASE
  #     WHEN {% condition date_comparison_filter %} ${transaction_raw} {% endcondition %} THEN 'This Week'
  #     WHEN ${transaction_raw} >= TIMESTAMP(DATE_ADD(CAST({% date_start date_comparison_filter %} AS DATE), INTERVAL -1 WEEK)) AND ${transaction_raw} < TIMESTAMP(DATE_ADD(CAST({% date_end date_comparison_filter %} AS DATE), INTERVAL -1 WEEK)) THEN 'Prior Week'
  #   END;;
  # }

}
