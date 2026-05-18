{{ config(materialized='view') }}

select *
from {{ source('raw', 'shipment_line_items') }}
