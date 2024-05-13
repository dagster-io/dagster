view: exception_derived_table {
  derived_table: {
    sql:
      SELECT
        *
      FROM `looker-private-demo.retail.us_stores`
      WHERE 1=1
        {% if _model._name == 'thelook' %} AND 1=1 {% endif %};;
  }
}
