{% set column_tests = {
	'phone': [
		sdf_test.not_null('err','phone')]
} %}
{% set table_tests = {
	'0': sdf_test.generate_column_tests('lineage.pub.middle', column_tests),
	'1': sdf_test.unique_columns('err','middle', ['&quot;user_id&quot;', '&quot;phone&quot;'])
} %}
{{ sdf_test.generate_table_tests('lineage.pub.middle', table_tests)  }}