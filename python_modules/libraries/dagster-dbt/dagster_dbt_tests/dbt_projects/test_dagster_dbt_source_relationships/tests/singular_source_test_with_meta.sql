-- A singular test that depends on both the `foo` and `bar` sources. Singular tests are not
-- attached to a node by dbt, so without the `meta.dagster.ref` escape hatch it would not be
-- modeled as an asset check. The escape hatch attaches the resulting asset check to the `bar`
-- source.
{{ config(meta={"dagster": {"ref": {"name": "bar", "package": "my_source"}}}) }}

select foo.id
from {{ source('my_source', 'foo') }} as foo
inner join {{ source('my_source', 'bar') }} as bar on foo.bar_id = bar.id
where foo.id is null
