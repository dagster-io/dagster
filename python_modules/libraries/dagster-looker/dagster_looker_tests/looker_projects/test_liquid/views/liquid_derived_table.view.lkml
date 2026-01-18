view: liquid_derived_table {
  derived_table: {
    sql:
      SELECT
        *
      FROM `looker-private-demo.retail.us_stores`
      WHERE 1=1
        {% if _model._name == 'thelook' %} AND 1=1 {% endif %}
        AND {% condition holiday %} holiday {% endcondition %}
        AND CONVERT_TIMEZONE('America/New_York', timestamp)::DATE BETWEEN
            COALESCE({% date_start us_stores.start_date %},  DATEADD(week, -1, {% date_end us_stores.end_date %}))
            AND COALESCE({% date_end us_stores.end_date %}, CONVERT_TIMEZONE('UTC', 'America/New_York', GETDATE()))
        ;;
  }
}
