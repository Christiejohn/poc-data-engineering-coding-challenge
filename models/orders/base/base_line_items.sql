{{ config(materialized='view') }}

select *
from {{ source('raw', 'line_items') }}
