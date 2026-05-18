{# DuckDB-flavored shim of Extend's get_incremental_value. #}
{# Returns max value of incr_col (timestamp) cast for use in incremental WHERE. #}
{% macro get_incremental_value(incr_col, relation=this) -%}
    {%- if execute and is_incremental() -%}
        {%- set query -%}
            select cast(max({{ incr_col }}) as varchar) from {{ relation }}
        {%- endset -%}
        {%- set result = run_query(query).columns[0].values()[0] -%}
        {%- if result -%}
            cast('{{ result }}' as timestamp)
        {%- else -%}
            cast('1900-01-01' as timestamp)
        {%- endif -%}
    {%- else -%}
        cast('1900-01-01' as timestamp)
    {%- endif -%}
{%- endmacro %}
