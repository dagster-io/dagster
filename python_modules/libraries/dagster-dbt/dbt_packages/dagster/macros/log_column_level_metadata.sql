{% macro log_column_level_metadata(enable_parent_relation_metadata_collection=true) %}
    -- This macro should only be run in the context of a `dagster-dbt` invocation.
    {%- set is_dagster_dbt_cli = env_var('DAGSTER_DBT_CLI', '') == 'true' -%}

    {%- if execute and is_dagster_dbt_cli -%}
        -- Retrieve the column metadata of the current node.
        {%- set columns = adapter.get_columns_in_relation(this) -%}
        {%- set column_schema = {} -%}

        {% for column in columns %}
            {%- set serializable_column = {column.name: {'data_type': column.data_type}} -%}
            {%- set _ = column_schema.update(serializable_column) -%}
        {%- endfor -%}

        -- For column level lineage, retrieve the column metadata of the current node's parents.
        -- The parents are defined by the current node's dbt refs and sources.
        {%- set parent_relations = [] -%}

        {%- for ref_args in model.refs -%}
            {%- set ref_relation = ref(ref_args['name'], package=ref_args.get('package'), version=ref_args.get('version'))-%}
            {%- set _ = parent_relations.append(ref_relation) -%}
        {%- endfor -%}

        {%- for source_args in model.sources -%}
            {%- set source_relation = source(source_args[0], sources_args[1])-%}
            {%- set _ = parent_relations.append(ref_relation) -%}
        {%- endfor -%}

        -- Return a structured log of
        -- {
        --     "relation_name": str,
        --     "columns": {
        --         <column_name>: {
        --             "data_type": str
        --         }
        --     },
        --     "parents": {
        --         <relation_name>: {
        --             "columns": {
        --                 <column_name>: {
        --                     "data_type": str
        --                 }
        --             }
        --         }
        --     }
        -- }
        --
        -- If `enable_parent_relation_metadata_collection` is set to `false`, the structured log
        -- will only contain the current node's column metadata.
        {%- set structured_log = {'relation_name': this.render(), 'columns': column_schema} -%}

        {%- if enable_parent_relation_metadata_collection -%}
            {%- set _ = structured_log.update({'parents': {}}) -%}

            {%- for parent_relation in parent_relations -%}
                {%- set parent_relation_columns = adapter.get_columns_in_relation(parent_relation) -%}
                {%- set parent_relation_column_schema = {} -%}

                {%- for column in parent_relation_columns -%}
                    {%- set serializable_column = {column.name: {'data_type': column.data_type}} -%}
                    {%- set _ = parent_relation_column_schema.update(serializable_column) -%}
                {%- endfor -%}

                {%- set structured_parent_relation_metadata = {parent_relation.render(): {'columns': parent_relation_column_schema}} -%}
                {%- set _ = structured_log['parents'].update(structured_parent_relation_metadata) -%}
            {%- endfor -%}
        {%- endif -%}

        {%- do log(tojson(structured_log), info=true) -%}
    {%- endif -%}
{% endmacro %}
