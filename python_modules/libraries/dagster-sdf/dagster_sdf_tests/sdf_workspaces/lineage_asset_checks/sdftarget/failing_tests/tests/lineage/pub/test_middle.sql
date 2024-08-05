{% set column_tests = {
	'phone': [
		sdf_test.like('err','phone', '&apos;non_existent_%&apos;'),
		sdf_test.in_accepted_values('err','phone', ['&apos;non_existent&apos;'])]
} %}
{% set table_tests = {
	'0': sdf_test.generate_column_tests('lineage.pub.middle', column_tests),
	'1': sdf_test.unique_columns('err','middle', ['&quot;user_id&quot;', '&quot;user_id&quot;'])
} %}
{{ sdf_test.generate_table_tests('lineage.pub.middle', table_tests)  }}